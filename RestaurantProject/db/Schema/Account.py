from sqlalchemy import Column, Integer, String, ForeignKey
from sqlalchemy.orm import relationship
from db.server import Base

class Account(Base):
    __tablename__ ='Account'

    #Primary Key
    UserID = Column(Integer, primary_key=True, autoincrement=True)

    #Foreign Keys
    LocationID = Column(Integer, ForeignKey('Location.LocationID'), nullable=False)

    #Other info in table 
    Email = Column(String(100))
    PhoneNumber = Column(String(10))
    Role = Column(String(40))
    Password = Column(String(256))


    def __repr__(self):
        return f""" User ID: {self.UserID}, Email ID: {self.Email}, Phone Number ID: {self.PhoneNumber}, Role: {self.Role}, Password: {self.Password}, 
        Location ID: {self.LocationID}"""