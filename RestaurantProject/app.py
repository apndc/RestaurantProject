landing
from flask import Flask, render_template, request, url_for, redirect, session

from flask import Flask, render_template, request, session, url_for, redirect
main
import os, bcrypt, logging
from sqlalchemy import func
from sqlalchemy.orm import joinedload
from dotenv import load_dotenv
from db.schema import EP_Verification, RO_Verification
from db.server import get_session
from db.query import *
from db.schema import *
from werkzeug.utils import secure_filename
from collections import defaultdict
from datetime import datetime, timedelta
from functools import wraps
load_dotenv()

os.makedirs("logs", exist_ok=True)

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "dev-key-chnange-me")
api_key = os.environ.get("GOOGLE_API_KEY", "")

# Setup for Logger
logging.basicConfig( 
    filename="logs/log.txt", level=logging.INFO, filemode="a", format="%(asctime)s [%(levelname)s] %(message)s"
)

logger = logging.getLogger(__name__)

# Stored Stuff For Methods
order = ["Appetizer", "Entree", "Dessert", "Drinks"]
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg'}

# Limit Extensions
def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# Derived Values To Pass Thru
def full_location(location):
    """ Return A Singular Location String """
    parts = [
        location.StreetName,
        location.City,
        location.State,
        location.ZipCode
    ]
    # Filter out any None or empty strings and join with commas
    return ", ".join(str(p) for p in parts if p)

# Home page: BookIt Welcome
@app.route('/')
def home():
    return render_template('bookit-welcome.html')

@app.route('/error')
def error():
    """Doc later"""
    errors = request.args.get('errors', 'Unknown error')
    return render_template('error.html', errors=errors)

@app.route('/createaccount', methods=["GET", "POST"])
def createaccount():
    error: str = None
    is_valid: bool = False

    if request.method == 'POST':
        # Make A Location
        
        db = get_session()
        
        location_data: dict = {}

        valid_location = False
        
        for key, value in request.form.items():
            if key == 'StreetName' or key == 'City' or key == 'State' or key == 'ZipCode':
                location_data[key] = value.strip()
        
        newLocation = Location(**location_data)
        
        try:
            db.add(newLocation)
            db.flush()
            location_id = newLocation.LocationID
            db.commit()
            valid_location = True
        except Exception as e:
                logging.error(f"An error has occurred: {e}")
                return redirect(url_for('error', errors=str(e)))
            
        # Validate user info
        FirstName=request.form["FirstName"].upper()
        LastName=request.form["LastName"].upper()
        PhoneNumber=request.form["PhoneNumber"].replace("-", "")
        Email=request.form["Email"].lower()
        Password=request.form["Password"]
        role=request.form["Role"].upper()

        if not (FirstName.isalpha() and LastName.isalpha()):
            return redirect(url_for('error', errors="Invalid name"))
        if not (PhoneNumber.isnumeric() and len(PhoneNumber) == 10):
            return redirect(url_for('error', errors="Invalid phone number"))

        # --- Step 3: Role verification for EP/RO ---
        if role in ['EVENT_PLANNER', 'RESTAURANT_OWNER']:
            verification_code = request.form.get('verification_code', '').strip().lower()

            if role == 'EVENT_PLANNER':
                record = session.query(EP_Verification).filter(
                    func.lower(EP_Verification.verification_code)==verification_code
                ).first()
            else:  # RESTAURANT_OWNER
                record = session.query(RO_Verification).filter(
                    func.lower(RO_Verification.verification_code)==verification_code
                ).first()

            if not record:
                return redirect(url_for('error', errors='Invalid verification credentials'))

        # --- Step 4: Hash password ---
        pw_bytes = Password.encode('utf-8')
        salt = bcrypt.gensalt()
        hashed_pw = bcrypt.hashpw(pw_bytes, salt)

        # --- Step 5: Insert user ---
        user_data = {
            'FirstName': FirstName,
            'LastName': LastName,
            'PhoneNumber': PhoneNumber,
            'Email': Email,
            'Password': hashed_pw,
            'Role': role,
            'LocationID': location_id
        }

        try:
            if not get_one(Account, Email=Email):
                insert(Account(**user_data))
            else:
                return redirect(url_for('error', errors="An account with this email already exists"))
        except Exception as e:
            logging.error(f"User creation error: {e}")
            return redirect(url_for('error', errors=str(e)))

        # --- Step 6: Role-based redirect ---
        if role == 'EVENT_PLANNER':
            return redirect(url_for('eventpage'))
        elif role == 'RESTAURANT_OWNER':
            return redirect(url_for('restaurant_page'))  # Or a dedicated RO dashboard
        else:
            return redirect(url_for('home'))

    # GET request: render signup page
    return render_template('createaccount.html')

#Delete SQL
@app.route('/delete', methods=["GET", "POST"])
def delete():
    error = None
    message = None
    if request.method == "POST":
        try:
            import codecs
            email = request.form.get("Email").lower().strip()

            user = get_one(Account, Email=email)

            userPw = request.form["Password"].encode('utf-8')
            
            if not user:
                error = "No account found with that email."
                logging.error(error)
            else:
                stored_hash_hex = user.Password
                stored_hash_bytes = codecs.decode(stored_hash_hex.replace("\\x", ""), "hex")
                
                if bcrypt.checkpw(userPw, stored_hash_bytes):
                    delete_one(user)
                    message = f"Account with email {email} has been deleted."
        except Exception as e:
            logging.error(f"Error deleting user:, {e}")
            error = "An error occured. Please try again"
        finally:
            db.close()
    return render_template("delete.html", error=error, message=message)

@app.route('/login', methods=["GET", "POST"])
def login():
    if request.method == 'POST':
        import codecs
        email = request.form["Email"].lower()
        password = request.form["Password"].encode('utf-8')

        try:
            # Get user by email
            attempted_user = get_one(Account, Email=email)

            if attempted_user is None:
                logging.error("No account found for that email.")
                return redirect(url_for('login'))

            stored_hash_hex = attempted_user.Password
            stored_hash_bytes = codecs.decode(stored_hash_hex.replace("\\x", ""), "hex")

landing
            if bcrypt.checkpw(userPw, stored_hash_bytes):
                session['user_email'] = attempted_user.Email
                return redirect(url_for('user_landing'))
            # Validate password
            if bcrypt.checkpw(password, stored_hash_bytes):
                # Redirect based on role (case-insensitive)
                role = attempted_user.Role.strip().lower()

                if role == 'event_planner':
                    logging.info(f"{email} logged in as Event Planner.")
                    return redirect(url_for('eventpage'))

                elif role == 'restaurant_owner':
                    logging.info(f"{email} logged in as Restaurant Owner.")
                    return redirect(url_for('restaurant_page'))

                else:
                    logging.warning(f"{email} has unknown role '{attempted_user.Role}'. Redirecting home.")
                    return redirect(url_for('home'))
main
            else:
                logging.error("Incorrect password.")
                return redirect(url_for('login'))

        except Exception as e:
            print(f"Login error: {e}")
            logging.exception(f"Error during login: {e}")
            return redirect(url_for('login'))

    return render_template('login.html')

@app.route('/profile')
def profile():
    # You can expand this later with user info
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    return render_template('profile.html', user_name=session.get('user_name'))

@app.route('/landing')
def user_landing():
    db = get_session()

    try: 
        upcoming = []
        try:
            upcoming = (
                db.query(Reservation).options(joinedload(Reservation.restaurant)).filter(Reservation.AccountID == session['user_id'], Reservation.DateTime >= datetime.utcnow())
                .order_by(Reservation.DateTime.asc()).limit(5).all()
            )
        except Exception:
            upcoming = []
        
        cuisines = ["Italian" , "Chinese", "American", "BBQ", "Mexican"]
        return render_template(
            'user_landing.html', api_key=api_key,
            user_name = session.get('user_name'), cuisines = cuisines, upcoming = upcoming
        )

    finally:
        db.close()

# General Events Page
@app.route('/event')
def eventpage():
    return render_template('bookit-eventpage.html', api_key=api_key)

# Event Page
@app.route('/event/<int:event_id>')
def events(event_id):
    return render_template('bookit-eventpage.html', api_key=api_key, event_id=event_id)

# Restaurant Overview
@app.route('/restaurant')
def restaurant_page():
    db = get_session()
    restaurants = db.query(RestaurantInfo).all()
    db.close()
    return render_template('bookit-restaurant.html', restaurants=restaurants, api_key=api_key)

# Dollar Filter for Formatting
@app.template_filter('dollars')
def dollars(value):
    return f"${value:,.2f}"

# Individual Restaurant Page
@app.route('/restaurant/<string:name>')
def restaurant(name):
    db = get_session()    
    restaurant = db.query(RestaurantInfo).filter_by(Name=name).first()
    location = restaurant.location
    fullLocation = full_location(location)
    menuItems = restaurant.menu
    categories = defaultdict(list)
    for item in menuItems:
        categories[item.Category].append(item)
    sorted_categories = sorted(categories.items(),
                           key=lambda kv: order.index(kv[0]) if kv[0] in order else len(order))
    html = render_template('bookit-restaurant-template.html',
                       restaurant=restaurant, location=location, menuItems=menuItems,
                         categories=sorted_categories, fullLocation=fullLocation)
    db.close()
    return html

# Reservation Page
@app.route('/reservation', methods=['GET', 'POST'])
def reservation():
    if request.method == 'POST':
        # Access form data
        name = request.form.get('name')
        phone = request.form.get('phone')
        email = request.form.get('email')
        special = request.form.get('special')
        card_number = request.form.get('cardNumber')
        name_on_card = request.form.get('nameOnCard')
        exp_date = request.form.get('expDate')
        cvv = request.form.get('cvv')
        updates = request.form.get('updates')

        # Here you can save to a database or process the reservation
        print(f"Reservation from {name}, phone {phone}, email {email}, special: {special}, updates: {updates}")

        return "Reservation submitted!"  # Or redirect to a confirmation page

    # GET request: render the reservation page
    return render_template('bookit-reservepage.html')

# TESTING STUFF DELETE LATER
@app.route('/test')
def test():
    return render_template('test.html')

#Debug stuff (given to us)
if __name__ == '__main__':
    app.run(debug=True)
