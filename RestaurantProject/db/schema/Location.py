from sqlalchemy import Column, Integer, String
from sqlalchemy.orm import relationship
from db.server import Base

class Location(Base):
    __tablename__= 'Location'

    LocationID = Column(Integer, primary_key=True, autoincrement=True)

    ZipCode= Column(Integer)
    City= Column(String(40))
    State= Column(String(2))
    StreetName= Column(String(40))

    #Relationships
    accounts = relationship("Account", back_populates="location")
    restaurants = relationship("RestaurantInfo", back_populates="location")

    def __repr__(self):
        return f""" Zip Code: {self.ZipCode}, City: {self.City}, State: {self.State}, Street Name: {self.StreetName}"""

    