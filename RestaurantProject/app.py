from flask import Flask, render_template, request, url_for, redirect, session
from flask import Flask, render_template, request, session, url_for, redirect
import os, bcrypt, logging
from sqlalchemy import func
from sqlalchemy.orm import joinedload
from sqlalchemy import func
from dotenv import load_dotenv
from db.schema import EP_Verification, RO_Verification
from db.server import get_session
from db.query import *
from db.schema import *
from werkzeug.utils import secure_filename
from collections import defaultdict
from functools import wraps
from filters import register_filters
load_dotenv()

app = Flask(__name__)

api_key = os.environ["GOOGLE_API_KEY"]
from datetime import datetime, timedelta
from functools import wraps
load_dotenv()

os.makedirs("logs", exist_ok=True)

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "dev-key-chnange-me")
api_key = os.environ.get("GOOGLE_API_KEY", "")

# Key + Session Setup for Cookies
app.secret_key = os.getenv("SECRET_KEY")

app.config.update(
    SESSION_COOKIE_HTTPONLY = True,
    SESSION_COOKIE_SECURE = False,
    SESSION_COOKIE_SAMESITE = "Lax",
    PERMANENT_SESSION_LIFETIME = 60 * 60 * 24  # The Cookie Lasts For 1 Day and Then Expires
)

# Setup for Logger
logging.basicConfig( 
    filename="logs/log.txt", level=logging.INFO, filemode="a", format="%(asctime)s [%(levelname)s] %(message)s"
)

logger = logging.getLogger(__name__)

# Stored Stuff For Methods
order = ["Appetizer", "Entree", "Dessert", "Drinks"]
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg'}

# Initialize Filters
register_filters(app)

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

# Loads Current User On Each Page Load
@app.before_request
def load_current_user():
    g.current_user = None
    uid = session.get("UserID")
    if uid is not None:
        g.current_user = get_one(Account, UserID=uid)

# Login Required Decorator
def login_required(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        if not session.get("UserID"):
            return redirect(url_for("login", next=request.path))
        return f(*args, **kwargs)
    return wrapper

def get_distance_miles(origin, **destinations):
    """
    origin, destination: full address strings
    returns: distance in miles (float) or None on failure
    """
    url = "https://maps.googleapis.com/maps/api/distancematrix/json"
    params = {
        "origins": origin,
        "destinations": destinations,
        "key": api_key,
        "units": "imperial"   
    }

    resp = requests.get(url, params=params)
    data = resp.json()

    try:
        element = data["rows"][0]["elements"][0]

        if element["status"] != "OK":
            return None

        miles_text = element["distance"]["text"]  
        
        miles = float(miles_text.replace("mi", "").strip())
        return miles

    except (KeyError, IndexError, ValueError):
        return None


def guest_required(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        if session.get("UserID"):
            return redirect(url_for("restaurant_page"))
        return f(*args, **kwargs)
    return wrapper
    
@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for('home'))


# Home page: BookIt Welcome
@app.route('/')
@guest_required
def home():
    return render_template('bookit-welcome.html')

@app.route('/error')
def error():
    """Doc later"""
    errors = request.args.get('errors', 'Unknown error')
    return render_template('error.html', errors=errors)

@app.route('/createaccount', methods=["GET", "POST"])
@guest_required
def createaccount():
    import re
    error = None

    if request.method == 'POST':
        # Make A Location
        
        PGsession = get_session()
        
        location_data: dict = {}

        newLocation = Location(**location_data)

        try:
            PGsession.add(newLocation)
            PGsession.flush()
            location_id = newLocation.LocationID
            PGsession.commit()
            valid_location = True
        except Exception as e:
                logging.error(f"An error has occurred: {e}")
                return render_template("createaccount.html", error=error)
        finally:
            PGsession.close()
        # Make A User
        FirstName=request.form["FirstName"].upper()
        LastName=request.form["LastName"].upper()
        PhoneNumber=request.form["PhoneNumber"]
        role = request.form.get("Role", "CUSTOMER").upper()

        if FirstName.isalpha() and LastName.isalpha() and PhoneNumber.isnumeric() and len(PhoneNumber) == 10:
            logging.info(f"Inputs {FirstName}, {LastName}, and {PhoneNumber} are valid.")
            is_valid = True
        elif not FirstName.isalpha():
            logging.info(f"Input: {FirstName} is Invalid")
            #error = error_msg

        if is_valid and valid_location:

            user_data: dict = {}

            user_data['LocationID'] = location_id

            for key, value in request.form.items():
                if key in ('FirstName', 'LastName', 'Role'):
                    user_data[key] = value.strip().upper()
                elif key == 'Email':
                    user_data[key] = value.strip().lower()
                elif key == 'PhoneNumber':
                    user_data[key] = value.strip().replace("-", "")
                elif key == 'Password':
                    user_data[key] = value.strip()
            
            user_data['Role'] = user_data.get('Role', 'CUSTOMER')

            # converting password to array of bytes
            bytes = user_data['Password'].encode('utf-8')

            # generating the salt
            salt = bcrypt.gensalt()

            # Hashing the password
            user_data['Password'] = bcrypt.hashpw(bytes, salt)

            try:
                if not get_one(Account, Email=user_data['Email']):
                    newUser = insert(Account(**user_data))
                else:
                    return render_template("createaccount.html", error="Already An Account With This Email")
            except Exception as e:
                logging.error(f"An error has occurred: {e}")
                return render_template("createaccount.html", error=error)
            
            # Clear all Cookies and Add Account ID to Session
            session.clear()
            session.permanent = True
            session['UserID'] = newUser.UserID
            
            # Additional Logging Info
            logging.info(f"User {newUser.UserID} created successfully.")
            
            role = (newUser.Role or "CUSTOMER").strip().upper()

            if role == "EVENT_PLANNER":
                return redirect(url_for('eventpage'))
            elif role == "RESTAURANT_OWNER":
                return redirect(url_for('restaurant_page'))
            else:
                # default: normal customer – you can change this to a /landing later
                return redirect(url_for('restaurant_page'))

    return render_template('createaccount.html', error=error)

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

#Login Page
@app.route('/login', methods=["GET", "POST"])
@guest_required
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

            if bcrypt.checkpw(userPw, stored_hash_bytes):
                # Clear all Cookies and Add Account ID to Session
                session.clear()
                session.permanent = True
                session['UserID'] = attempted_user.UserID
                
                # Additional Logging Info
                logging.info(f"User {attempted_user.Email} logged in successfully.")
                
                return redirect(url_for('restaurant_page'))
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
@login_required
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
@login_required
def restaurant_page():

    session = get_session()
    
    try:
        sort = request.args.get('sort', 'name')

        restaurants = session.query(RestaurantInfo).all()
        
        
        user_location = session.query(Location).filter_by(LocationID = g.current_user.LocationID).first()
        user_full_address = full_location(user_location)
        
        for r in restaurants:
            r.full_address = full_location(r.location)
            r.distance_miles = get_distance_miles(user_full_address, r.full_address)

        # Sorts
        if sort == 'name':
            restaurants = sorted(restaurants, key=lambda r: r.Name.lower())
        elif sort == 'rating':
            ...
            #restaurants = sorted(restaurants, key=lambda r: r.Rating or 0, reverse=True)
        elif sort == 'distance':
            restaurants = sorted(
                restaurants,
                key=lambda r: r.distance_miles if r.distance_miles is not None else 1e9
            )
        # add sort for cuisine

        return render_template('bookit-restaurant.html',restaurants=restaurants,current_sort=sort, api_key=api_key)
    finally:
        session.close()

# Individual Restaurant Page
@app.route('/restaurant/<int:restaurant_id>')
@login_required
def restaurant(restaurant_id):
    session = get_session()    
    restaurant = session.query(RestaurantInfo).filter_by(RID=restaurant_id).first()
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
@login_required
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

# Profile Page
@app.route('/profile')
@login_required
def profile():
    user = g.current_user
    return render_template('profile.html', user=user)

cuisine_list = ['Italian', 'Chinese', 'Mexican', 'Indian', 'French', 'Japanese', 'Mediterranean', 'Thai', 'Spanish', 'Greek']

@app.route('/restaurantform', methods=['GET', 'POST'])
@login_required
def restaurant_form():
    error = None
    message = None
    if request.method == 'POST':
        try:
            # Fields are UserID, LocationID, Name, Description PhoneNumber, Cuisine, Capacity, Fee
            user_id = g.current_user.UserID
            name = request.form.get('Name')
            description = request.form.get('Description')
            phone_number = request.form.get('PhoneNumber')
            cuisine = request.form.get('Cuisine')
            capacity = int(request.form.get('Capacity'))
            fee = float(request.form.get('Fee'))

            # Create a default location for now
            PGsession = get_session()
        
            location_data: dict = {}

            valid_location = False
            
            for key, value in request.form.items():
                if key in ('StreetName', 'City', 'State', 'ZipCode'):
                    location_data[key] = value.strip()
            
            newLocation = Location(**location_data)
            
            try:
                PGsession.add(newLocation)
                PGsession.flush()
                location_id = newLocation.LocationID
                logging.info(location_id)
                PGsession.commit()
                valid_location = True
            except Exception as e:
                    logging.error(f"An error has occurred: {e}")
                    return render_template("createaccount.html", error=error)
            finally:
                PGsession.close()

            if valid_location:
                new_restaurant = RestaurantInfo(
                    UserID=user_id,
                    LocationID=location_id,
                    Name=name,
                    Description=description,
                    PhoneNumber=phone_number,
                    Cuisine=cuisine,
                    Capacity=capacity,
                    Fee=fee
                )
                insert(new_restaurant)
                message = "Restaurant added successfully!"
        except Exception as e:
            logging.error(f"Error adding restaurant: {e}")
            error = "An error occurred while adding the restaurant."
    return render_template("bookit-restaurant-form.html", error=error, message=message, cuisines=cuisine_list)

# TESTING STUFF DELETE LATER
@app.route('/test')
def test():
    return render_template('test.html')

#Debug stuff (given to us)
if __name__ == '__main__':
    app.run(debug=True)
