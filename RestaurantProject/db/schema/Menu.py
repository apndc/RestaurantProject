from sqlalchemy import Column, Integer, String, ForeignKey, Numeric, Text
from sqlalchemy.orm import relationship
from db.server import Base

class Menu(Base):
    __tablename__ = 'Menu'

    RID = Column(Integer, ForeignKey('RestaurantInfo.RID'), nullable=False, primary_key=True)

    ItemName = Column(String(40), primary_key=True)

    Price = Column(Numeric(10,2))

    Category = Column(String(40))
    
    Description = Column(Text)

    # Relationships
    restaurants = relationship("RestaurantInfo", back_populates="menu")

    def __repr__(self):
        return f""" RID: {self.RID}, ItemName: {self.ItemName}, Price: {self.Price}, Category: {self.Category}, 
        Description: {self.Description}"""