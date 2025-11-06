import csv, os
from db.server import get_session
from db.schema import *

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
    


importData("Location")
importData("Account")
importData("CardInfo")
importData("RestaurantInfo")
importData("Reservation")
importData("Events")
importData("Menu")