"""query.py: leverages SQLAlchemy to create generic queries for interacting with the postgres DB"""
from db.server import get_session

def get_all(table) -> list:
    """Select all records from a DB table using SQLAlchemy ORM.

        args: 
            table (object): db table

        returns:
            records (list[obj]): list of records from db table
    """
    session = get_session()
    try:
        # get all records in the table
        records = session.query(table).all()
        return records
    
    finally:
        session.close()

def insert(record) -> None:
    """Insert One Record into a Table
    """
    session = get_session()

    try: 
        session.add(record)
        session.commit()
    
    except Exception as e:
        session.rollback()
        print("Error Inserting Records:", e)
    
    finally:
        session.close()

def get_one(table, **filters) -> object:
    """
    Select One Record From The DB Table
    """
    session = get_session()
    try:
        record = session.query(table).filter_by(**filters).first()
        return record
    finally:
        session.close()

def delete_one(record):

    session = get_session()

    try: 
        session.delete(record)
        session.commit()
    except Exception as e:
        session.rollback()
        print("Error Inserting Records:", e)
    finally:
        session.close()