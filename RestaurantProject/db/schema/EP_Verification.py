from sqlalchemy import Column, Integer, String
from db.server import Base

class EP_Verification(Base):
    __tablename__ = 'ep_verification'

    id = Column(Integer, primary_key=True)
    verification_code = Column(String, nullable=False)
