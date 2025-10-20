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
    

