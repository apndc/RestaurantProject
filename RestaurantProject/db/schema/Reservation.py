from sqlalchemy import Column, Integer, String, ForeignKey, Date, Time
from sqlalchemy.orm import relationship
from db.server import Base

class Reservation(Base):
    __tablename__ = 'Reservation'

    # Primary Key
    ReservationID = Column(Integer, primary_key=True, autoincrement=True)

    # Foreign Keys
    UserID = Column(Integer, ForeignKey('Account.UserID'), nullable=False)
    RID = Column(Integer, ForeignKey('RestaurantInfo.RID'), nullable=False)

    # Relationships
    user = relationship("Account", back_populates="reservations")
    restaurant = relationship("RestaurantInfo", back_populates="reservations")
    event = relationship("Events", back_populates="reservation", uselist=False)

    # Reservation Information
    NumberOfGuests = Column(Integer, nullable=False)

    ReservationDate = Column(Date, nullable=False)      # YYYY-MM-DD
    ReservationTime = Column(Time, nullable=False)      # HH:MM:SS

    # Optional Fields
    SpecialOccasion = Column(String(255), nullable=True)     # e.g., Birthday
    SpecialRequests = Column(String(500), nullable=True)     # e.g., Allergies, wheelchair access

    def __repr__(self):
        return (
            f"Reservation ID: {self.ReservationID}, "
            f"User ID: {self.UserID}, Restaurant ID: {self.RID}, "
            f"Guests: {self.NumberOfGuests}, "
            f"Date: {self.ReservationDate}, Time: {self.ReservationTime}, "
            f"Occasion: {self.SpecialOccasion}, Requests: {self.SpecialRequests}"
        )