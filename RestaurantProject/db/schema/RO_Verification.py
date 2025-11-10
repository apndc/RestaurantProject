from sqlalchemy import Column, Integer, String
from . import Base 

class RO_Verification(Base):
    __tablename__ = 'ro_verification'

    id = Column(Integer, primary_key=True)
    email = Column(String, unique=True, nullable=False)
    verification_code = Column(String, nullable=False)
