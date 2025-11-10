# populate_verification.py
from db.server import get_session
from db.schema import EP_Verification, RO_Verification

session = get_session()

# Clear existing entries (optional)
session.query(EP_Verification).delete()
session.query(RO_Verification).delete()

# Add dummy credentials
ep_record = EP_Verification(email="eventplanner@test.com", verification_code="abc456")
ro_record = RO_Verification(email="restaurantowner@test.com", verification_code="xyz123")

session.add_all([ep_record, ro_record])

session.commit()
session.close()

print("Verification tables populated with dummy data!")
