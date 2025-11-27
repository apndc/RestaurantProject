from db.schema import *  # imports Account, Reservation, Events, etc.
from db.server import Base, engine

def reset_all():
    # ensure all models are registered with Base.metadata

    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)

    print("Tables reset!")

reset_all()