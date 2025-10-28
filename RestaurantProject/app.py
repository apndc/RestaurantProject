from flask import Flask, render_template, request
import os
from sqlalchemy.orm import joinedload
from dotenv import load_dotenv
from db.server import get_session
from db.schema import *
from werkzeug.utils import secure_filename
from collections import defaultdict
load_dotenv()

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
        location.Zipcode
    ]
    # Filter out any None or empty strings and join with commas
    return ", ".join(str(p) for p in parts if p)

app = Flask(__name__)

# Home page: BookIt Welcome
@app.route('/')
def home():
    return render_template('bookit-welcome.html')

# General Events Page
@app.route('/event')
def eventpage():
    api_key = os.environ["GOOGLE_API_KEY"]
    return render_template('bookit-eventpage.html', api_key=api_key)

# Event Page
@app.route('/event/<int:event_id>')
def events(event_id):
    api_key = os.environ["GOOGLE_API_KEY"]
    return render_template('bookit-eventpage.html', api_key=api_key, event_id=event_id)

# Restaurant Overview
@app.route('/restaurant')
def restaurant_page():
    session = get_session()
    restaurants = session.query(RestaurantInfo).all()
    session.close()
    api_key = os.environ["GOOGLE_API_KEY"]
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


if __name__ == '__main__':
    app.run(debug=True)
