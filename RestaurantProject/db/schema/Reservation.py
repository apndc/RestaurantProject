from sqlalchemy import Column, Integer, String, ForeignKey, DateTime
from sqlalchemy.orm import relationship
from db.server import Base

class Reservation(Base):
    __tablename__ ='Reservation'

    #Primary Key
    ReservationID = Column(Integer, primary_key=True, autoincrement=True)

    #Foreign Keys
    UserID = Column(Integer, ForeignKey('Account.UserID'), nullable=False)
    RID = Column(Integer, ForeignKey('RestaurantInfo.RID'), nullable=False)

    #Relationships
    user = relationship("Account", back_populates="reservations")
    restaurant = relationship("RestaurantInfo", back_populates="reservations")
    event = relationship("Events", back_populates="reservation", uselist=False)

    #Other info in table 
    NumberOfGuests = Column(Integer)
    #Date + Time of Reservation
    Date = Column(DateTime, nullable=False)

    def __repr__(self):
        return f""" Reservation ID: {self.ReservationID}, User ID: {self.UserID}, Restaurant ID: {self.RID}, Number of Guests: {self.NumberOfGuests}, 
        Date: {self.Date}"""