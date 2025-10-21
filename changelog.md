# CHANGES [v1.1.0]:

### ***REQUIRED FIXES***
* DROP ALL TABLES BEFORE RUNNING APP.PY (You can use drop_all.py)
    * 'python -m db.schema.imports.reset_tables' will **DROP AND RECREATE ALL TABLES**
### **Added Changes**
#### Importer With Dummy Data (Thanks GPT for your help)
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