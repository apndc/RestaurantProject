from sqlalchemy import Column, Integer, String, ForeignKey
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
    PhoneNumber = Column(String(10))
    Cusine = Column(String(40))
    Capacity = Column(Integer)
    Fee = Column(Integer)

    def __repr__(self):
        return f""" Restuarnt ID: {self.RID}, User ID: {self.UserID}, Locaction ID: {self.LocationID}, Phone Number: {self.PhoneNumber}, 
        Cusine: {self.Cusine}, Capacity: {self.Capacity}, Fee: {self.Fee}"""