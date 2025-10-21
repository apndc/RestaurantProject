from sqlalchemy import Column, Integer, String, ForeignKey
from sqlalchemy.orm import relationship
from db.server import Base

class CardInfo(Base):
    __tablename__ ='CardInfo'

    #Primary Key
    CardID = Column(Integer, primary_key=True, autoincrement=True)

    #Foreign Keys
    UserID = Column(Integer, ForeignKey('Account.UserID'), nullable=False)

    #Other info in table 
    CardNum = Column(String(19))
    ZipCode = Column(Integer)
    Name = Column(String(100))
    Date = Column(String(5))
    CVV = Column(String(4))

    #Relationships
    account = relationship("Account", back_populates="cards")

    def __repr__(self):
        return f""" Card ID: {self.CardID}, User ID: {self.UserID}, Card Number: {self.CardNum}, Zip Code: {self.ZipCode}, 
        Name: {self.Name}, Date: {self.Date}, CVV: {self.CVV}"""
