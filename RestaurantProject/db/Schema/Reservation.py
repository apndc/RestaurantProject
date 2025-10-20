from sqlalchemy import Column, Integer, String, ForeignKey
from sqlalchemy.orm import relationship
from db.server import Base

class Reservation(Base):
    __tablename__ ='Reservation'

    #Primary Key
    ReservationID = Column(Integer, primary_key=True, autoincrement=True)

    #Foreign Keys
    UserID = Column(Integer, ForeignKey('Account.UserID'), nullable=False)
    RID = Column(Integer, ForeignKey('RestaurantInfo.RID'), nullable=False)

    #Other info in table 
    NumberOfGuests = Column(Integer)
    Time = Column(String(5))

    def __repr__(self):
        return f""" Reservation ID: {self.ReservationID}, User ID: {self.UserID}, Resturarnt ID: {self.RID}, Number of Guests: {self.NumberOfGuests}, 
        Time: {self.Time}"""