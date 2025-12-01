import csv, os

from db.server import get_session
from db.schema import *
from db.schema import Base, EP_Verification, RO_Verification
from .reset_tables import reset_all

reset_all()


def readFile(fileName):
    with open(f"db/schema/imports/{fileName}.csv", newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)  # honors quotes, commas, headers
        rows = []
        for row in reader:
            # drop empty lines
            if not any(v and v.strip() for v in row.values()):
                continue
            rows.append({k.strip(): (v.strip() if isinstance(v, str) else v) for k, v in row.items()})
        return rows

def importData(dataName):
    all_rows = readFile(dataName)
    session = get_session()
    try:
        model_class = globals()[dataName]
        for fields in all_rows:
            obj = model_class(**fields)
            session.add(obj)
        session.commit()
        print(f"Successfully Imported {dataName}")
    except Exception as e:
        session.rollback()
        print(f"Error inserting {dataName}", e)
    finally:
        session.close()
    
def populate_verification():
    session = get_session()
    try:
        # Clear old data first
        session.query(EP_Verification).delete()
        session.query(RO_Verification).delete()
        session.commit()

        # Insert dummy codes
        ep_codes = ['ABC456']
        ro_codes = ['XYZ123']

        for code in ep_codes:
            session.add(EP_Verification(verification_code=code))
        for code in ro_codes:
            session.add(RO_Verification(verification_code=code))

        session.commit()
        print("Verification tables populated!")
    except Exception as e:
        session.rollback()
        print("Error populating verification tables:", e)
    finally:
        session.close()

importData("Location")
importData("Account")
importData("CardInfo")
importData("RestaurantInfo")
importData("Reservation")
importData("Events")
importData("Menu")

# --------------------------
# Populate verification tables last
# --------------------------
populate_verification()