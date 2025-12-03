from sqlalchemy import Column, Integer, String, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from . import Base 

class EP_Reservation(Base):
    __tablename__ = 'EP_Reservation'

    # Primary key
    id = Column(Integer, primary_key=True, autoincrement=True)

    # Foreign key references
    UserID = Column(Integer, ForeignKey('Account.UserID'), nullable=False)  # customer who booked
    EPID = Column(Integer, ForeignKey('Account.UserID'), nullable=False)    # assigned Event Planner

    # Event details
    FirstName = Column(String(50), nullable=False)
    LastName = Column(String(50), nullable=False)
    PhoneNumber = Column(String(20), nullable=False)
    EventType = Column(String(100), nullable=False)
    Guests = Column(Integer, nullable=False)
    DateTime = Column(DateTime, nullable=False)

    # Relationships (optional)
    customer = relationship("Account", foreign_keys=[UserID])
    event_planner = relationship("Account", foreign_keys=[EPID])
