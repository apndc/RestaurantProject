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

def insert(record) -> object:
    """Insert One Record into a Table
    """
    session = get_session()

    try: 
        session.add(record)
        session.commit()
        session.refresh(record)
        return record
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

def delete_one(model, **filters):
    session = get_session()
    try:
        obj = session.query(model).filter_by(**filters).first()
        if obj:
            session.delete(obj)
            session.commit()
    except Exception as e:
        session.rollback()
        print("Error deleting record:", e)
    finally:
        session.close()