import csv, os
from db.server import get_session
from db.schema import *

def readFile(fileName):
    with open(f"db/schema/imports/{fileName}.csv", "r") as file:
        lines = file.readlines()
        all_rows = []
        for i, line in enumerate(lines):
            line = line.strip()
            elements = line.split(',')
            if i == 0:
                headers = elements
            else:
                row = dict(zip(headers, elements))
                all_rows.append(row)
        return all_rows

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