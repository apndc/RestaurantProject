from flask import Flask, render_template, request, url_for, redirect, session
from flask import Flask, render_template, request, session, url_for, redirect
from flask import flash
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
from datetime import datetime, timedelta, date
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
    import re
    error = None

    if request.method == "POST":
        db = get_session()

        # Save Location
        location_data = {
        key: value.strip()
        for key, value in request.form.items()
        if key in ['StreetName', 'City', 'State', 'ZipCode']
        }

        newLocation = Location(**location_data)

        try:
            db.add(newLocation)
            db.flush()
            location_id = newLocation.LocationID
            db.commit()
        except Exception as e:
            logging.error(f"Location creation error: {e}")
            return redirect(url_for('error', errors=str(e)))
            
        # Validate user info
        FirstName = request.form["FirstName"].strip()
        LastName = request.form["LastName"].strip()
        PhoneNumber = request.form["PhoneNumber"].replace("-", "")
        Email = request.form["Email"].lower()
        Password = request.form["Password"]
        role = request.form.get("Role", "").upper()

        # --- Step 1: Name validation ---
        name_pattern = re.compile(r"^[A-Za-z'-]+$")

        if not (name_pattern.match(FirstName) and name_pattern.match(LastName)):
            error = "INVALID NAME"
            return render_template("createaccount.html", error=error)

        # --- Step 2: Phone validation ---
        if not (PhoneNumber.isnumeric() and len(PhoneNumber) == 10):
            error = "INVALID PHONE NUMBER"
            return render_template("createaccount.html", error=error)
            
        # --- Step 3: Role verification for EP/RO ---
        if role in ['EVENT_PLANNER', 'RESTAURANT_OWNER']:
            verification_code = request.form.get("verification_code", "").strip().lower()

            if role == 'EVENT_PLANNER':
                record = db.query(EP_Verification).filter(
                    func.lower(EP_Verification.verification_code) == verification_code
                ).first()

            else:
                record = db.query(RO_Verification).filter(
                    func.lower(RO_Verification.verification_code) == verification_code
                ).first()

            if not record:
                error = "INVALID VERIFICATION CREDENTIALS"
                return render_template("createaccount.html", error=error)
               

        # --- Step 4: Hash password ---
        pw_bytes = Password.encode('utf-8')
        salt = bcrypt.gensalt()
        hashed_pw = bcrypt.hashpw(pw_bytes, salt)

        # --- Step 5: Insert user ---
        if get_one(Account, Email=Email):
            error = "An account with this email already exists"
            return render_template("createaccount.html", error=error)

        try:
            insert(Account(
                FirstName=FirstName.upper(),
                LastName=LastName.upper(),
                PhoneNumber=PhoneNumber,
                Email=Email,
                Password=hashed_pw,
                Role=role,
                LocationID=location_id
            ))
        except Exception as e:
            logging.error(f"User creation error: {e}")
            return redirect(url_for("error", errors=str(e)))
        
        # Retrieve user & set session for the 'login' route
        user = get_one(Account, Email=Email)
        session["user_id"] = user.UserID
        session["user_email"] = user.Email
        session["user_name"] = f"{user.FirstName} {user.LastName}"

        # --- Step 6: Role-based redirect ---
        if role == "EVENT_PLANNER":
            return redirect(url_for("eventpage"))
        elif role == "RESTAURANT_OWNER":
            return redirect(url_for("restaurant_page"))
        else:
            #default = normal customer
            return redirect(url_for("user_landing"))
        
    # GET request: render signup page
    return render_template('createaccount.html')

# Delete current logged-in user
@app.route('/delete', methods=["POST"])
def delete():
    if 'user_id' not in session:
        return redirect(url_for('login'))

    db = get_session()
    error = None
    message = None

    try:
        # Get the logged-in user
        user = db.query(Account).filter_by(UserID=session['user_id']).first()

        if not user:
            error = "User not found."
            logging.error(error)
        else:
            # Delete user row
            db.delete(user)
            db.commit()
            message = "Your account has been deleted successfully."

            # Clear session
            session.clear()

            # Redirect to welcome page
            return redirect(url_for('home'))

    except Exception as e:
        logging.error(f"Error deleting user: {e}")
        error = "An error occurred. Please try again."

    finally:
        db.close()

    # fallback if something went wrong
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

            if not bcrypt.checkpw(password, stored_hash_bytes):
                logging.error("Incorrect password.")
                return redirect(url_for('login'))
            
            # Login successful >> Set session
            session['user_id'] = attempted_user.UserID
            session['user_email'] = attempted_user.Email
            session['user_name'] = f"{attempted_user.FirstName} {attempted_user.LastName}"
            
            role = attempted_user.Role.strip().lower()

            if role == "event_planner":
                return redirect(url_for("eventpage"))

            elif role == "restaurant_owner":
                return redirect(url_for("restaurant_page"))

            elif role == "customer":
                return redirect(url_for("user_landing"))
           
            else:
                return redirect(url_for("home"))

        except Exception as e:
            logging.exception(f"Login error: {e}")
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

    # --- Protect user without session ---
    if "user_id" not in session:
        return redirect(url_for("login"))

    db = get_session()

    try:
        today = date.today()

        try:
            upcoming = (
                db.query(Reservation)
                .options(joinedload(Reservation.restaurant))
                .filter(
                    Reservation.UserID == session['user_id'],
                    Reservation.ReservationDate >= today
                )
                .order_by(Reservation.ReservationDate.asc(),
                          Reservation.ReservationTime.asc())
                .limit(5)
                .all()
            )
        except Exception as e:
            print("Error getting reservations:", e)
            upcoming = []

        cuisines = ["Italian", "Chinese", "American", "BBQ", "Mexican"]

        return render_template(
            "user_landing.html",
            api_key=api_key,
            user_name=session.get("user_name", ""),
            cuisines=cuisines,
            upcoming=upcoming
        )
    finally:
        db.close()

''' SHOWS UPCOMING RESERVATIONS, NOTHING ELSE
@app.route('/landing')
def user_landing():
    db = get_session()

    try: 
        upcoming = []
        try:
            upcoming = (
                db.query(Reservation)
                .options(joinedload(Reservation.restaurant))
                .filter(
                    Reservation.UserID == session['user_id'],
                    Reservation.ReservationDate >= datetime.utcnow().date()
                )
                .order_by(Reservation.ReservationDate.asc(), Reservation.ReservationTime.asc())
                .limit(5)
                .all()
            )
        except Exception:
            upcoming = []

        cuisines = ["Italian", "Chinese", "American", "BBQ", "Mexican"]

        return render_template(
            'user_landing.html',
            api_key=api_key,
            user_name=session.get('user_name'),
            cuisines=cuisines,
            upcoming=upcoming
        )

    finally:
        db.close()
'''
''' OLD LANDING SAVE TILL FINAL
@app.route('/landing')
def user_landing():
    db = get_session()

    try: 
        upcoming = []
        try:
            upcoming = (
                db.query(Reservation).options(joinedload(Reservation.restaurant)).filter(Reservation.UserID == session['user_id'], Reservation.DateTime >= datetime.utcnow())
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
'''        
# logout function for username on landing page
@app.route('/logout')
def logout():
    """Log out the current user and redirect to Welcome page"""
    session.clear() 
    return redirect(url_for('home'))

# Edit account function for username on landing page
@app.route('/edit_account', methods=['GET', 'POST'])
def edit_account():
    """View and update the logged-in user's account information"""
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    db = get_session()
    user = db.query(Account).filter_by(UserID=session['user_id']).first()
    
    if request.method == 'POST':
        # update fields from form
        user.FirstName = request.form['FirstName'].strip().upper()
        user.LastName = request.form['LastName'].strip().upper()
        user.PhoneNumber = request.form['PhoneNumber'].replace("-", "")
        user.Email = request.form['Email'].lower()
        db.commit()
        
        # update session name
        session['user_name'] = f"{user.FirstName} {user.LastName}"
        
        return redirect(url_for('user_landing'))
    
    return render_template('edit_account.html', user=user)

# General Events Page
@app.route('/event')
def eventpage():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    # Pull First Name from database
    user_id = session['user_id']
    user = get_one(Account, UserID=user_id)
    first_name = f"{user.FirstName}" if user else "My Profile"
    
    return render_template('bookit-eventpage.html', user_name=first_name, api_key=api_key)

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

@app.route('/reservation', methods=['POST'])
def reservation():
    if 'user_id' not in session:
        return redirect(url_for('login'))

    db = get_session()

    try:
        # Required fields from the form
        user_id = session['user_id']
        restaurant_id = int(request.form['RID'])
        date_str = request.form['date']
        time_str = request.form['time']
        guests = int(request.form['guests'])

        # Optional fields
        occasion = request.form.get('event', None)
        special_requests = request.form.get('accommodations', None)

        # Combine date + time into one datetime object
        reservation_datetime = datetime.strptime(
            f"{date_str} {time_str}",
            "%Y-%m-%d %H:%M"
        )

        # Create a new reservation object
        new_reservation = Reservation(
            UserID=user_id,
            RID=restaurant_id,
            NumberOfGuests=guests,
            ReservationDate=date_str,     
            ReservationTime=time_str,      
            SpecialOccasion=occasion,
            SpecialRequests=special_requests
        )

        db.add(new_reservation)
        db.commit()
        flash("Reservation placed!", "success")
        return redirect(url_for('user_landing'))

    except Exception as e:
        db.rollback()
        flash("Oops! Something went wrong.", "error")
        logging.error(f"Reservation error: {e}")
        return redirect(url_for('error', errors=str(e)))

    finally:
        db.close()

# TESTING STUFF DELETE LATER
@app.route('/test')
def test():
    return render_template('test.html')

#Debug stuff (given to us)
if __name__ == '__main__':
    app.run(debug=True)
