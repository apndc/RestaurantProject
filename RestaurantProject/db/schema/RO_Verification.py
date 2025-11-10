from sqlalchemy import Column, Integer, String
from db.schema.__init__ import Base  # Adjust import if needed

class RO_Verification(Base):
    __tablename__ = 'ro_verification'

    id = Column(Integer, primary_key=True)
    email = Column(String, unique=True, nullable=False)
    verification_code = Column(String, nullable=False)
