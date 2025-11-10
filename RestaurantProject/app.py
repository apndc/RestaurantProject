from flask import Flask, render_template, request, url_for, redirect, session, g
import os, bcrypt, logging
from sqlalchemy.orm import joinedload
from dotenv import load_dotenv
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
    error: str = None
    is_valid: bool = False

    if request.method == 'POST':
        # Make A Location
        
        PGsession = get_session()
        
        location_data: dict = {}

        valid_location = False
        
        for key, value in request.form.items():
            if key == 'StreetName' or key == 'City' or key == 'State' or key == 'ZipCode':
                location_data[key] = value.strip()
        
        newLocation = Location(**location_data)
        
        try:
            PGsession.add(newLocation)
            PGsession.flush()
            location_id = newLocation.LocationID
            PGsession.commit()
            valid_location = True
        except Exception as e:
                logging.error(f"An error has occurred: {e}")
                return redirect(url_for('error', errors=str(e)))
        finally:
            PGsession.close()
        # Make A User
        FirstName=request.form["FirstName"].upper()
        LastName=request.form["LastName"].upper()
        PhoneNumber=request.form["PhoneNumber"]

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
                if key == 'FirstName' or key == 'LastName' or key == 'Role':
                    user_data[key] = value.strip().upper()
                elif key == 'Email':
                    user_data[key] = value.strip().lower()
                elif key == 'PhoneNumber':
                    user_data[key] = value.strip().replace("-", "")
                elif key == 'Password':
                    user_data[key] = value.strip()
            
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
                    return redirect(url_for('error', errors="Already An Account With This Email"))
            except Exception as e:
                logging.error(f"An error has occurred: {e}")
                return redirect(url_for('error', errors=str(e)))
            
            # Clear all Cookies and Add Account ID to Session
            session.clear()
            session.permanent = True
            session['UserID'] = newUser.UserID
            
            # Additional Logging Info
            logging.info(f"User {newUser.UserID} created successfully.")
            
            return redirect(url_for('restaurant_page'))

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

#Login Page
@app.route('/login', methods=["GET", "POST"])
@guest_required
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
                # Clear all Cookies and Add Account ID to Session
                session.clear()
                session.permanent = True
                session['UserID'] = attempted_user.UserID
                
                # Additional Logging Info
                logging.info(f"User {attempted_user.Email} logged in successfully.")
                
                return redirect(url_for('restaurant_page'))
            else:
                logging.error(f"Wrong Password")
        except Exception as e:
            logging.error(f"An error has occurred: {e}")
            return redirect(url_for('login'))
        
    return render_template('login.html')

# General Events Page
@app.route('/event')
@login_required
def eventpage():
    return render_template('bookit-eventpage.html', api_key=api_key)

# Event Page
@app.route('/event/<int:event_id>')
def events(event_id):
    return render_template('bookit-eventpage.html', api_key=api_key, event_id=event_id)

# Restaurant Overview
@app.route('/restaurant')
@login_required
def restaurant_page():
    session = get_session()
    restaurants = session.query(RestaurantInfo).all()
    session.close()
    return render_template('bookit-restaurant.html', restaurants=restaurants, api_key=api_key)

# Individual Restaurant Page
@app.route('/restaurant/<string:name>')
@login_required
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
            fee = int(request.form.get('Fee'))
            # Create a default location for now
            default_location = Location(StreetName="123 Default St", City="DefaultCity", State="DS", ZipCode="00000")
            inserted_location = insert(default_location)
            location_id = inserted_location.LocationID
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
