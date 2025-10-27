"""query.py: leverages SQLAlchemy to create generic queries for interacting with the postgres DB"""
from db.server import get_session

def get_all(table) -> list:
    session = get_session()
    try:
        # get all records in the table
        records = session.query(table).all()
        return records
    finally:
        session.close()

def get_one(table, **filters) -> object:
    session = get_session()
    try:
        record = session.query(table).filter_by(**filters).first()
        return record
    finally:
        session.close()


def insert(record) -> None:
        session = get_session()
        try:
            #insert one new record
            session.add(record)
            # 'save' the changes
            session.commit()
        except Exception as e:
            session.rollback()
            print("Error inserting records: ", e)

        finally:
            session.close()

