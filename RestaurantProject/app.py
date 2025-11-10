from flask import Flask, render_template, request, url_for, redirect
import os, bcrypt, logging
from sqlalchemy.orm import joinedload
from dotenv import load_dotenv
from RestaurantProject.db.schema import EP_Verification, RO_Verification
from db.server import get_session
from db.query import *
from db.schema import *
from werkzeug.utils import secure_filename
from collections import defaultdict
load_dotenv()

api_key = os.environ["GOOGLE_API_KEY"]

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

app = Flask(__name__)

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
        
        session = get_session()
        
        location_data: dict = {}

        valid_location = False
        
        for key, value in request.form.items():
            if key == 'StreetName' or key == 'City' or key == 'State' or key == 'ZipCode':
                location_data[key] = value.strip()
        
        newLocation = Location(**location_data)
        
        try:
            session.add(newLocation)
            session.flush()
            location_id = newLocation.LocationID
            session.commit()
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
            verification_email = request.form.get('verification_email', '').lower().strip()
            verification_code = request.form.get('verification_code', '').strip()

            if role == 'EVENT_PLANNER':
                record = session.query(EP_Verification).filter_by(
                    email=verification_email, verification_code=verification_code
                ).first()
            else:  # RESTAURANT_OWNER
                record = session.query(RO_Verification).filter_by(
                    email=verification_email, verification_code=verification_code
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
            return redirect(url_for('eventplanner_page'))
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
    return render_template("delete.html", error=error, message=message)

@app.route('/login', methods=["GET", "POST"])
def login():
    if request.method == 'POST':
        try:
            import codecs
            # Get SQLAlchemy Object And See If The Email + Pass Combo Exists 
            attempted_user = get_one(Account, Email=request.form["Email"].lower())
            userPw = request.form["Password"].encode('utf-8')
            
            stored_hash_hex = attempted_user.Password
            stored_hash_bytes = codecs.decode(stored_hash_hex.replace("\\x", ""), "hex")

            if bcrypt.checkpw(userPw, stored_hash_bytes):
                return redirect(url_for('home'))
            else:
                logging.error(f"Wrong Password")
        except Exception as e:
            logging.error(f"An error has occurred: {e}")
            return redirect(url_for('login'))
        
    return render_template('login.html')

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
    session = get_session()
    restaurants = session.query(RestaurantInfo).all()
    session.close()
    return render_template('bookit-restaurant.html', restaurants=restaurants, api_key=api_key)

# Dollar Filter for Formatting
@app.template_filter('dollars')
def dollars(value):
    return f"${value:,.2f}"

# Individual Restaurant Page
@app.route('/restaurant/<string:name>')
def restaurant(name):
    session = get_session()    
    restaurant = session.query(RestaurantInfo).filter_by(Name=name).first()
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
    session.close()
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
