# ensure all models are registered with Base.metadata
from db.schema import *  # imports Account, Reservation, Events, etc.
from db.server import Base, engine

Base.metadata.drop_all(bind=engine)
Base.metadata.create_all(bind=engine)

print("Tables reset!")