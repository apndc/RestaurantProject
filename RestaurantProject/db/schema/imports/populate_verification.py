from db.server import get_session, engine  # make sure your engine is imported
from db.schema import Base, EP_Verification, RO_Verification

# Create tables in the database if they don't exist
Base.metadata.create_all(engine)

session = get_session()

# Clear old data (optional)
session.query(EP_Verification).delete()
session.query(RO_Verification).delete()
session.commit()

# Insert dummy verification codes
ep_codes = ['ABC456', 'DEF123']
ro_codes = ['XYZ123', 'LMN789']

for code in ep_codes:
    session.add(EP_Verification(verification_code=code))

for code in ro_codes:
    session.add(RO_Verification(verification_code=code))

session.commit()
session.close()
print("Verification tables populated!")
