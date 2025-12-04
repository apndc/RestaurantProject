from flask import Flask, render_template, request, url_for, redirect, session, g, flash
import os, bcrypt, logging, requests
from sqlalchemy import func
from sqlalchemy.orm import joinedload
from dotenv import load_dotenv
from db.server import get_session
from db.query import *
from db.schema import *
from werkzeug.utils import secure_filename
from collections import defaultdict
from functools import wraps
from filters import register_filters
from datetime import datetime, timedelta
from email_validator import validate_email, EmailNotValidError
load_dotenv()

# Stored Stuff For Methods
order = ["Appetizer", "Entree", "Dessert", "Drinks"]
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg'}
cuisine_list = ['Italian', 'Chinese', 'Mexican', 'Indian', 'French', 'Japanese', 'Mediterranean', 'Thai', 'Spanish', 'Greek']

api_key = os.environ["GOOGLE_API_KEY"]

os.makedirs("logs", exist_ok=True)

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
        # If user is logged in, do NOT show the guest page
        if session.get("UserID"):
            return redirect(url_for("dashboard"))
        return f(*args, **kwargs)
    return wrapper

def owner_required(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        user = getattr(g, "current_user", None)
        role = (getattr(user, "Role", "") or "").strip().upper()
        if user is None or role != "RESTAURANT_OWNER":
            return redirect(url_for("dashboard"))
        return f(*args, **kwargs)
    return wrapper


def customer_required(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        user = getattr(g, "current_user", None)
        role = (getattr(user, "Role", "") or "").strip().upper()
        if user is None or role != "CUSTOMER":
            return redirect(url_for("dashboard"))
        return f(*args, **kwargs)
    return wrapper


def event_required(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        user = getattr(g, "current_user", None)
        role = (getattr(user, "Role", "") or "").strip().upper()
        if user is None or role != "EVENT_PLANNER":
            return redirect(url_for("dashboard"))
        return f(*args, **kwargs)
    return wrapper


def get_distance_miles(origin, destinations):
    """
    origin: full address strings
    destinations: dict of destination full addresses
    returns: distance from origin in miles (float) or None on failure for each address given
    """
    
    if not destinations:
        return []

    # Google expects destinations as a pipe-separated string
    destinations_param = "|".join(destinations)

    url = "https://maps.googleapis.com/maps/api/distancematrix/json"
    params = {
        "origins": origin,
        "destinations": destinations_param,
        "key": api_key,
        "units": "imperial"   
    }

    resp = requests.get(url, params=params)
    data = resp.json()

    results = []

    try:
        elements = data["rows"][0]["elements"]
        for el in elements:
            if el.get("status") != "OK":
                results.append(None)
                continue

            # "distance": {"text": "2.4 mi", "value": 3865}
            meters = el["distance"]["value"]  
            miles = meters / 1609.34          
            
            results.append(miles)

    except (KeyError, IndexError, ValueError):
        results = [None] * len(destinations)

    return results

# Setup for Logger
logging.basicConfig( 
    filename="logs/log.txt", level=logging.INFO, filemode="a", format="%(asctime)s [%(levelname)s] %(message)s"
)

logger = logging.getLogger(__name__)

def create_app():
    app = Flask(__name__)

    # Key + Session Setup for Cookies
    app.secret_key = os.getenv("SECRET_KEY")

    app.config.update(
        SESSION_COOKIE_HTTPONLY = True,
        SESSION_COOKIE_SECURE = False,
        SESSION_COOKIE_SAMESITE = "Lax",
        PERMANENT_SESSION_LIFETIME = 60 * 60 * 24  # The Cookie Lasts For 1 Day and Then Expires
    )

    # Initialize Filters
    register_filters(app)

    # Loads Current User On Each Page Load
    @app.before_request
    def load_current_user():
        g.current_user = None
        uid = session.get("UserID")
        if uid is not None:
            g.current_user = get_one(Account, UserID=uid)


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
            PGsession = get_session()
            location_data: dict = {}

            # Collect location info
            for key, value in request.form.items():
                if key in ('StreetName', 'City', 'State', 'ZipCode'):
                    location_data[key] = value.strip()

            newLocation = Location(**location_data)
            valid_location = False
            is_valid = False

            # Insert Location
            try:
                PGsession.add(newLocation)
                PGsession.flush()
                location_id = newLocation.LocationID
                PGsession.commit()
                valid_location = True
            except Exception as e:
                logging.error(f"Location error: {e}")
                return render_template("createaccount.html", error="Error saving location.")
            finally:
                PGsession.close()

            # User info
            FirstName = request.form["FirstName"].strip().upper()
            LastName = request.form["LastName"].strip().upper()
            PhoneNumber = request.form["PhoneNumber"].strip()
            role = request.form.get("Role", "CUSTOMER").upper()

            # Basic validation
            if FirstName.isalpha() and LastName.isalpha() and PhoneNumber.isnumeric() and len(PhoneNumber) == 10:
                is_valid = True
            else:
                if not FirstName.isalpha():
                    error = 'First name can only contain letters'
                elif not LastName.isalpha():
                    error = 'Last name can only contain letters'
                elif not PhoneNumber.isnumeric() or len(PhoneNumber) != 10:
                    error = 'Phone number must be exactly 10 digits'

            if not (is_valid and valid_location):
                return render_template('createaccount.html', error=error)

            # Collect user data
            user_data: dict = {'LocationID': location_id}
            for key, value in request.form.items():
                if key in ('FirstName', 'LastName', 'Role'):
                    user_data[key] = value.strip().upper()
                elif key == 'Email':
                    try:
                        v = validate_email(value)
                        user_data[key] = v.normalized
                    except EmailNotValidError:
                        return render_template('createaccount.html', error='Invalid email format')
                elif key == 'PhoneNumber':
                    user_data[key] = value.strip().replace("-", "")
                elif key == 'Password':
                    user_data[key] = value.strip()

            user_data['Role'] = user_data.get('Role', 'CUSTOMER')

            # Password hashing
            password_bytes = user_data['Password'].encode('utf-8')
            salt = bcrypt.gensalt()
            user_data['Password'] = bcrypt.hashpw(password_bytes, salt)

            # --- Verification Checks ---
            if role == "EVENT_PLANNER":
                code_entered = request.form.get("verification_code", "").strip().upper()
                ep_row = get_one(EP_Verification, verification_code=code_entered)
                if not ep_row:
                    return render_template("createaccount.html", error="Invalid Event Planner verification code")

            elif role == "RESTAURANT_OWNER":
                code_entered = request.form.get("verification_code", "").strip().upper()
                ro_row = get_one(RO_Verification, verification_code=code_entered)
                if not ro_row:
                    return render_template("createaccount.html", error="Invalid Restaurant Owner verification code")

            # Insert user into Account
            try:
                if not get_one(Account, Email=user_data['Email']):
                    newUser = insert(Account(**user_data))
                else:
                    return render_template("createaccount.html", error="Already an account with this email")
            except Exception as e:
                logging.error(f"Account insertion error: {e}")
                return render_template("createaccount.html", error="Error creating account")

            # Setup session
            session.clear()
            session.permanent = False
            session['UserID'] = newUser.UserID
            logging.info(f"User {newUser.UserID} ({newUser.Role}) created successfully.")

            # Redirect based on role
            if newUser.Role == "EVENT_PLANNER":
                return redirect(url_for('eventpage'))
            elif newUser.Role == "RESTAURANT_OWNER":
                return redirect(url_for('owner_landing'))
            else:
                return redirect(url_for('dashboard'))

        return render_template('createaccount.html', error=error)


    # Delete current logged-in user
    @app.route('/delete')
    @login_required
    def delete():
        
        delete_one(Account, UserID=g.current_user.UserID)
        session.clear()
        
        return redirect(url_for('home'))

    # Login Page
    @app.route('/login', methods=["GET", "POST"])
    @guest_required
    def login():
        error_msg = None  # Initializes error message for incorrect login modal

        if request.method == 'POST':
            import codecs
            email = request.form["Email"].lower()
            password = request.form["Password"].encode('utf-8')

            try:
                # Get user by email
                attempted_user = get_one(Account, Email=email)
                userPw = request.form["Password"].encode('utf-8')

                if attempted_user is None:
                    logging.error("No account found for that email.")
                    error_msg = "No account found for that email."  # Set error message

                else:
                    stored_hash_hex = attempted_user.Password
                    stored_hash_bytes = codecs.decode(stored_hash_hex.replace("\\x", ""), "hex")

                    if bcrypt.checkpw(userPw, stored_hash_bytes):
                        # Successful login
                        session.clear()
                        session.permanent = False  # expires on browser close
                        session['UserID'] = attempted_user.UserID

                        logging.info(f"User {attempted_user.Email} logged in successfully.")
                        return redirect(url_for('dashboard'))
                    else:
                        error_msg = "Invalid Password."  # Set error message

                # If error_msg is set, render login template to trigger modal
                if error_msg:
                    return render_template('login.html', error_msg=error_msg)

            except Exception as e:
                logging.exception(f"Login error: {e}")
                error_msg = "An unexpected error occurred."
                return render_template('login.html', error_msg=error_msg)

        # GET request: show login page
        return render_template('login.html')


    @app.route('/landing')
    @login_required
    @customer_required
    def user_landing():
        db = get_session()

        try: 
            upcoming = []
            upcoming_ep = []
            try:
                # Restaurant Reservations
                upcoming = (
                    db.query(Reservation)
                    .options(joinedload(Reservation.restaurant))
                    .filter(
                        Reservation.UserID == session['UserID'], 
                        Reservation.DateTime >= datetime.utcnow()
                    )
                    .order_by(Reservation.DateTime.asc())
                    .limit(5)
                    .all()
                )
                
                # Event Planner Reservations
                upcoming_ep = (
                    db.query(EP_Reservation)
                    .filter(
                        EP_Reservation.UserID == session['UserID'],
                        EP_Reservation.DateTime >= datetime.utcnow()
                    )
                    .order_by(EP_Reservation.DateTime.asc())
                    .limit(5)
                    .all()
                )

            except Exception:
                upcoming = []
                upcoming_ep = []
                
            # Combine and sort both by Date and Time
            all_upcoming = sorted(
                upcoming + upcoming_ep,
                key=lambda x: x.DateTime
            )
            
            all_upcoming = all_upcoming[:5] # <--- limit of 5 for beginning purposes

            # Fetch event planners
            event_planners = (
                db.query(Account)
                .filter(Account.Role == 'EVENT_PLANNER')
                .all()
            )

            return render_template(
                'user_landing.html',
                api_key=api_key,
                user_name=session.get('user_name'),
                cuisines=cuisine_list,
                upcoming=upcoming,
                event_planners=event_planners  # Added For Event Planner reservation
            )

        finally:
            db.close()
            
    @app.route('/select_event_planner', methods=['POST'])
    @login_required
    @customer_required
    def select_event_planner():
        db = get_session()

        try:
            ep_id = request.form.get('ep_id')

            if not ep_id:
                flash("Invalid Event Planner selection.", "error")
                return redirect(url_for('user_landing'))

            # Ensure EP exists and is actually an event planner
            ep = db.query(Account).filter(
                Account.UserID == ep_id,
                Account.Role == "EVENT_PLANNER"
            ).first()

            if not ep:
                flash("Selected Event Planner not found.", "error")
                return redirect(url_for('user_landing'))

            # Store selected EP in session so next page can use it
            session["selected_event_planner_id"] = ep.UserID

            # Redirect user to fill out event form
            return redirect(url_for('event_form'))

        finally:
            db.close()
            
    @app.route('/create_event', methods=['POST'])
    @login_required
    @customer_required
    def create_event():
        db = get_session()
        try:
            ep_id = request.form['ep_id']
            first = request.form['FirstName'].strip()
            last = request.form['LastName'].strip()
            phone = request.form['PhoneNumber'].strip()
            event_type = request.form['EventType'].strip()
            guests = int(request.form.get('Guests', 0))  # safer
            dt = datetime.fromisoformat(request.form['DateTime'])

            # Create EP Reservation record
            new_event = EP_Reservation(
                UserID=session['UserID'],
                EPID=ep_id,
                FirstName=first,
                LastName=last,
                PhoneNumber=phone,
                EventType=event_type,
                Guests=guests,
                DateTime=dt
            )

            db.add(new_event)
            db.commit()
            
            # Fetch the Event Planner's name
            ep_user = db.query(Account).filter_by(UserID=ep_id).first()
            ep_name = f"{ep_user.FirstName} {ep_user.LastName}" if ep_user else "your Event Planner"

            # Flash personalized success message
            flash(f"Event with {ep_name} scheduled successfully!", "success")

            # Redirect to user landing page after success
            return redirect(url_for('user_landing'))

        except Exception as e:
            db.rollback()  # undo any partial changes
            logging.exception("Failed to create EP event")  # log error
            return "Error creating event", 500  

        finally:
            db.close()


    def redirect_dashboard():

        user = getattr(g, "current_user", None)
        if user is None:
            # Session is stale or user deleted – force login
            return redirect(url_for("login"))

        role = (user.Role or "").strip().lower()

        if role == 'event_planner':
            return redirect(url_for('eventpage'))
        elif role == 'restaurant_owner':
            return redirect(url_for('owner_landing'))
        else:
            return redirect(url_for('user_landing'))

            
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
        
        db = get_session()
        user = db.query(Account).filter_by(UserID=session['UserID']).first()
        
        # Fetch location object so Pylance knows it exists
        location = db.query(Location).filter_by(LocationID=user.LocationID).first()
        
        if request.method == 'POST':
            # update fields from form
            user.FirstName = request.form['FirstName'].strip().upper()
            user.LastName = request.form['LastName'].strip().upper()
            user.PhoneNumber = request.form['PhoneNumber'].replace("-", "")
            user.Email = request.form['Email'].lower()
            
            # Update location fields
            location.StreetName = request.form.get('StreetName', location.StreetName).strip()
            location.City = request.form.get('City', location.City).strip()
            location.State = request.form.get('State', location.State).strip()
            location.ZipCode = request.form.get('ZipCode', location.ZipCode).strip()
            
            db.commit()
            
            return redirect(url_for('dashboard'))
        
        # Include location in template context
        return render_template('edit_account.html', user=user, location=location)

    # General Events Page
    @app.route('/event')
    @login_required
    @event_required
    def eventpage():
        
        return render_template('bookit-eventpage.html', api_key=api_key)

    # Event Page
    @app.route('/event/<int:event_id>')
    @login_required
    @event_required
    def events(event_id):
        return render_template('bookit-eventpage.html', api_key=api_key, event_id=event_id)

    # Restaurant Overview
    @app.route('/restaurant')
    @login_required
    @customer_required
    def restaurant_page():

        PGsession = get_session()
        
        try:
            sort = request.args.get('sort', 'name')

            restaurants = PGsession.query(RestaurantInfo).all()
            
            
            user_location = PGsession.query(Location).filter_by(LocationID = g.current_user.LocationID).first()
            user_full_address = full_location(user_location)
            
            for r in restaurants:
                r.full_address = full_location(r.location)
                
            batch_addresses = [r.full_address for r in restaurants]
            
            distances = get_distance_miles(user_full_address, batch_addresses)

            for i, r in enumerate(restaurants):
                r.distance_miles = distances[i]

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
            PGsession.close()

    # Individual Restaurant Page
    @app.route('/restaurant/<int:restaurant_id>')
    @login_required
    def restaurant(restaurant_id):
        PGsession = get_session()    
        restaurant = PGsession.query(RestaurantInfo).filter_by(RID=restaurant_id).first()
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
        PGsession.close()
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
        return render_template('profile.html')

    @app.route('/restaurantform', methods=['GET', 'POST'])
    @login_required
    @owner_required
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
    
    
    @app.route('/owner_landing')
    @login_required
    @owner_required
    def owner_landing():
        db = get_session()

        try:
            user = g.current_user
            if user.Role.strip().lower() != 'restaurant_owner':
                return redirect(url_for('home'))

            restaurants=(
                db.query(RestaurantInfo).filter(RestaurantInfo.UserID == user.UserID).all()
            )

            return render_template(
                'owner_landing.html', user_name=f"{user.FirstName} {user.LastName}", restaurants=restaurants
            )
        finally:
            db.close()

    @app.route('/dashboard')
    @login_required
    def dashboard():
        return redirect_dashboard()

    return app

#Debug stuff (given to us)
if __name__ == '__main__':
    app = create_app()
    app.run(debug=True)
