# utils.py
# 🏢 UPDATED MASTER LOGISTICS TEMPLATE MATRIX (29 COLUMNS FIXED)

COLUMNS = [
    "Date", "Category", "Customer", "Agent", "HBL", "Liner", "Booking_MBL", 
    "Container", "POL", "POD", "ETD_as_per_SO", "ETD_ATD", "ETA_ATA", 
    "Follow_up_remarks", "Next_Follow_up", "HBL_Remarks", "Revenue_to_be_Billed", 
    "SO", "Empty container pickup", "Laden containers gatein", "SOB", 
    "Draft BL Checking and Approval", "Pre-alert documents", "Remittance", 
    "Telex/original bl", "FC", "Odex filing/manual", "Invoice", "DO", 
    "Empty containers return"
]

STAGES = [
    "Yet to sail",
    "On water",
    "Reached shore yet to release",
    "Released",
    "Empty container returned"
]
