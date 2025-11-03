from flask import Flask, render_template, request
import os
from dotenv import load_dotenv
load_dotenv()

app = Flask(__name__)

# Home page: BookIt Welcome
@app.route('/')
def index():
    return render_template('bookit-welcome.html')

@app.route('/users')
def users():
    """Users page: displays all users in the Users table"""
    all_users = get_all(Users)
        
    return render_template('users.html', users=all_users)

#Create Account
@app.route('/createaccount', methods=["GET", "POST"])
def createaccount():
    if request.method == 'POST':
        try:
            user = Users(FirstName = request.form["FirstName"],
            LastName = request.form["LastName"],
            Email = request.form ["Email"],
            PhoneNumber = request.form["PhoneNumber"],
            Location = request.form["Location"],
            StreetName = request.form["StreetName"],
            City = request.form["City"],
            State = request.form["State"],
            ZipCode = request.form["ZipCode"],
            Password = request.form["Password"])

            insert(user)
            return redirect(url_for('home'))
        except Exception as e:
                print("Error inserting user:", e)
    return render_template('createaccount.html')


#Log In Page
@app.route('/login', methods=["GET", "POST"])
def login():
    if request.method == 'POST':
        Email = request.form.get("Email")
        Password = request.form.get("Password")
        try:
            user = get_one(Users, Email=email)

            if user and user.Password == Password:
                return redirect(url_for('home'))

        except Exception as e:
                print("Error during login:", e)
                return render_template('login.html', error="An error occured. Please try again.")
    return render_template('login.html')

# Event Page
@app.route('/event')
def eventpage():
    api_key = os.environ["GOOGLE_API_KEY"]
    return render_template('bookit-eventpage.html', api_key=api_key)

# Restaurant Page
@app.route('/restaurant')
def restaurant():
    return render_template('bookit-restaurant.html')

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

