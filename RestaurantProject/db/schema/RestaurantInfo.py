from sqlalchemy import Column, Integer, String, ForeignKey, Text
from sqlalchemy.orm import relationship
from db.server import Base

class RestaurantInfo(Base):
    __tablename__ ='RestaurantInfo'

    #Primary Key
    RID = Column(Integer, primary_key=True, autoincrement=True)

    #Foreign Keys
    UserID = Column(Integer, ForeignKey('Account.UserID'), nullable=False)
    LocationID = Column(Integer, ForeignKey('Location.LocationID'), nullable=False)

    #Other info in table 
    Name = Column(String(40))
    Description = Column(Text)
    PhoneNumber = Column(String(10))
    Cuisine = Column(String(40))
    Capacity = Column(Integer)
    Fee = Column(Integer)

    #Relationships
    reservations = relationship("Reservation", back_populates="restaurant")
    owner = relationship("Account", back_populates="restaurants", uselist=False)
    location = relationship("Location", back_populates="restaurants", uselist=False)
    menu = relationship("Menu", back_populates="restaurants", cascade="all, delete-orphan")

    def __repr__(self):
        return f""" Restuarnt ID: {self.RID}, User ID: {self.UserID}, Location ID: {self.LocationID}, Phone Number: {self.PhoneNumber}, 
        Cuisine: {self.Cuisine}, Capacity: {self.Capacity}, Fee: {self.Fee}"""