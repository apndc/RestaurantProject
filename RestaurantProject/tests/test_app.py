import pytest

#Valid Data To Pass Through To Avoid Repetition
validAddress = {
    'StreetName':'Newbury Street',
    'State':'NY',
    'City':'Kingston',
    'ZipCode':'12456'
}
validUser = {
    'FirstName': 'John',
    'LastName': 'Doe',  
    'Email': 'wwasd@gmail.com',
    'PhoneNumber': '1234567890',
    'Password': 'password123'
}

def test_valid_signup(client):
    """Test Signup Functions Normally"""
    response = client.post('/createaccount', data= {
        **validAddress,
        **validUser
    })


def test_invalid_last_name(client):
    """Test signup validation for invalid last name"""
    response = client.post('/createaccount', data={
        'FirstName': 'John',
        'LastName': 'Doe123',  
        'Email': 'wwasd@gmail.com',
        'PhoneNumber': '1234567890',
        'Password': 'password123',
        **validAddress
    })
    assert b'Last name can only contain letters' in response.data

def test_invalid_email_login(client):
    """Tests login validation for invalid email"""
    response = client.post('/login', follow_redirects = False, data={
        'Email': '123',
        'Password': '123Pass'
    })
    assert response.status_code == 302
    assert "/login" in response.headers["Location"]

def test_invalid_email_signup(client):
    """Tests signup validation for invalid email"""
    response = client.post('/createaccount', data={
        'FirstName': 'John',
        'LastName': 'Doe',  
        'Email': 'wwasd@',
        'PhoneNumber': '1234567890',
        'Password': 'password123',
        **validAddress
    })
    assert b'Emails have to be formatted properly' in response.data

def test_login_page(client):
    """Test that success page loads"""
    response = client.get('/login')
    assert response.status_code == 200

def test_signup_page(client):
    """Test that error page loads"""
    response = client.get('/createaccount')
    assert response.status_code == 200

def test_home_page(client):
    """Test that home page loads"""
    response = client.get('/')
    assert response.status_code == 200

def test_login_page(client):
    """Test that home page loads"""
    response = client.get('/login')
    assert response.status_code == 200

def test_restaurant_page_logged_out(client):
    """Test that users page loads"""
    response = client.get('/restaurant', follow_redirects = False)
    # 302 is the Code for being Redirected
    assert response.status_code == 302
    assert "/login" in response.headers["Location"]

def test_restaurant_logged_in(client):
    # Fake login by setting session["UserID"]
    with client.session_transaction() as s:
        s["UserID"] = 1  

    response = client.get('/restaurant', follow_redirects=True)
    assert response.status_code == 200

def test_invalid_first_name(client):
    """Test signup validation for invalid first name"""
    response = client.post('/createaccount', data={
        'FirstName': '123',  # invalid - contains numbers
        'LastName': 'Doe',
        'Email': 'test@test.com',
        'PhoneNumber': '1234567890',
        'Password': 'password123',
        **validAddress
    })
    assert b'First name can only contain letters' in response.data

def test_invalid_phone_number_signup(client):
    """Test signup validation for invalid phone number"""
    response = client.post('/createaccount', data={
        'FirstName': 'John',
        'LastName': 'Doe',
        'Email': 'test@test.com',
        'PhoneNumber': '123',  # invalid - not 10 digits
        'Password': 'password123',
        **validAddress
    })
    assert b'Phone number must be exactly 10 digits' in response.data