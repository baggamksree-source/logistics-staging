# ==============================================================================
# GLOBAL CORE SCHEMAS & CONFIGURATION LOGISTICS PLATFORM MATRIX
# ==============================================================================

# Ironclad tracking headers matching row 1 of your master sheet layout perfectly
COLUMNS = [
    "Date", "Category", "Customer", "Agent", "HBL", "Liner", "Booking_MBL", 
    "Container", "POL", "POD", "ETD_as_per_SO", "ETD_ATD", "ETA_ATA", 
    "Follow_up_remarks", "Next_Follow_up", "HBL_Remarks", 
    "CFS_Nomination_De_Stuffing", "FC", "Revenue_to_be_Billed", 
    "Revenue_yet_to_be_Billed", "Created_By", "Last_Updated_By", "Last_Modified_On",
    "Nomination Certificate Acceptance", "Carting / Cargo Gate-in Pass", 
    "Shipping Instructions (SI) Cut-off", "Draft HBL Approval Loop", 
    "Verified Gross Mass (VGM) Submission", "Form 13 / Export Customs Gate Open", 
    "On-Board Bill of Lading (OBL) Issuance", "Carrier Invoice Settlement Request", 
    "Pre-Alert & Manifest Filing", "Delivery Order (DO) Document Release", 
    "Import Customs Clearance Filing", "De-Stuffing Nomination & Return"
]

# Trimmed stages starting strictly from verified cargo nomination
STAGES = [
    "Yet to sail",
    "On water",
    "Reached shore yet to release",
    "Released",
    "Empty container returned"
]

# Core post-nomination milestones used by your daily cloud email scanner
DOCS = {
    "OBL_Status": "Original Bill of Lading (OBL)",
    "DO_Status": "Delivery Order (DO)",
    "Customs_Cleared": "Customs Clearance Status",
    "Billing_Done": "Invoicing & Financial Settlement"
}

def get_header_map():
    return {
        "date": "Date", "stage": "Category", "category": "Category", 
        "customer": "Customer", "client": "Customer", "hbl": "HBL", 
        "liner": "Liner", "shipping line": "Liner", "mbl": "Booking_MBL", 
        "booking": "Booking_MBL", "container": "Container", "pol": "POL", 
        "pod": "POD", "etd": "ETD_as_per_SO", "eta": "ETA_ATA", 
        "revenue": "Revenue_to_be_Billed"
    }
