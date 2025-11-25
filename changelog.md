## TO-DO:
* Fix Some Filters
* Add Menu Items
* Add Route Decorators That Specifically Make Pages Available Based On Role
* Fix Routing + Merge ***User Land*** + ***Restaurant Listings*** 

# CHANGES [v3.1.1]:
* Changed `import.py` To Also Reset Tables Beforehand To Ensure
    * Also Fixed `Reservation` Import csv
* Fixed `get_distance_miles`
* Fixed Cookies + User Routing

# CHANGES [v3.1.0]: 
* Added Full Date and Time Field to Reservation
* Cookie for Login and Signup to Stay Logged In
* Login Specific Page Locking
* Template for Header
* Started Filter Functionality
* Reverted Restaurant Routes to Use The RID instead of Name
    * Makes Sure Duplicate Names Can Have Seperate Pages and Links

# CHANGES [v2.1.0]: Templating and Page Generation

# FINAL COMMIT
## <b>RELOAD TABLES AND RERUN IMPORTS AS USUAL | ADD logs Folder</b> 
## Added: 
* Login -> Connected to DB 
* Signup -> Connected to DB
* Delete -> Connected to DB
# To-Do List:
* Add More Client Side Locking
* <i>Make It Look Cool</i>
* Confirmation for Delete
# COMMIT 1
## **NEW TABLE**
    Testing with a Menu Table to load Menu Items Per Page
## "Schema" -> "schema"
    Fixed Paths
## Restaurant Table
* Added New <i><b>Name</b></i> and <i><b>Description</b></i> Fields
    * <b>RELOAD TABLES AGAIN BEFORE USE</b>
* Also Changed the Import Script To Work With The New Data Type (has the same functionality)
## APP.PY
* Extended Routes to Support Each Restaurant 
## Google Api
* Moved API Script Out To A Separate js file

# CHANGES [v2.0.0 BETA]: Front-End / Back-End Integration
## Started Adding Front End
* Still Needs To Be Integrated Properly
(Just so we can have a consistent starting point)

# CHANGES [v1.1.0]: Table Fixed + Data Scripting

### ***REQUIRED FIXES***
* DROP ALL TABLES BEFORE RUNNING APP.PY (You can use drop_all.py)
    * 'python -m db.schema.imports.reset_tables' will **DROP AND RECREATE ALL TABLES**
    * WILL NOT WORK IF FOLDER IS NAMED "Schema" WITH A CAPITAL 'S'
    * OR IF ANY OF THE INITIALIZED DB FILES ARE MISSPELLED
### **Added Changes**
#### Importer With Dummy Data 
    Run 'python -m db.schema.imports.import' from the RestaurantProject folder
#### In All Schemas:
    Added Relationships To Enforce Back-Population
#### In RestaurantInfo.py:
    Fixed Mislabeled Field Name
#### In CardInfo.py:
    Changed Some Integer Types -> Strings
        - If A Card Number Or CCV Starts With A Zero, The Integer Type Will Get Rid Of It

### **Misc. Changes**
Fixed Some other Minor repr String Elements