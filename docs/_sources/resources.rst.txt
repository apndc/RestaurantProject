.. _`Resources`:

Resources
=========

This section describes modules, classes, and functions private to the BookIt application. 
It is intended to document how the application works internally.


app.py
------
Initializes Flask app, configures routes, manages app decorators, and handles user sessions and cookies.


db.schema
---------
Contains SQLAlchemy ORM models:

- Account  
- Location  
- RestaurantInfo  
- Menu  
- CardInfo (not yet implemented)
- Events
- EP_Verification
- EP_Reservation 
- RO_Verification
- Reservation

Defines database table structure and relationships used throughout the application.


db.query
-----------
Creates the database engine and session factory. Provides:

- insert(): inserts and commits records to the database  
- get_one(): retrieves a single record based on filters  
- get_all(): retrieves multiple records based on filters
- delete_one(): deletes a single record based on filters

db.server
----------------------
- get_session(): returns a single SQLAlchemy session  
- init_database(): Initialize database tables

templates/
----------
Jinja2 templates and other HTML files used to render web pages for the application.


static/
--------
Static files including CSS, JS Scripts, and other Assets used in the application.

docs/
-----
Documentation files for the project including Sphinx configuration and reStructuredText files.

logs/
-----
Application log files for debugging and monitoring. 
(Not included in Git versions but is created on App launch)

tests/
------
Unit tests written with pytest.  
Covers:

- Validate Signup Form Inputs 
- Validate Login Logic
- Tests That Ensure Pages Load Properly



