from sqlalchemy import Column, Integer, String
from db.server import Base 

class RO_Verification(Base):
    __tablename__ = 'ro_verification'

    id = Column(Integer, primary_key=True)
    verification_code = Column(String, nullable=False)
