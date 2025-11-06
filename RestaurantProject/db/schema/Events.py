from sqlalchemy import Column, Integer, String, ForeignKey
from sqlalchemy.orm import relationship
from db.server import Base

class Events(Base):
    __tablename__ ='Events'

    #Primary Key
    EventID = Column(Integer, primary_key=True, autoincrement=True)

    #Foreign Keys
    ReservationID = Column(Integer, ForeignKey('Reservation.ReservationID'), nullable=False)

    #Other info in table 
    TypeOfEvent = Column(String(40))

    #Relationships
    reservation = relationship("Reservation", back_populates="event")

    def __repr__(self):
        return f""" Event ID: {self.EventID}, Reservation ID: {self.ReservationID}, Type of Event: {self.TypeOfEvent}"""