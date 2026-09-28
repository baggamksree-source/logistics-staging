# ==============================================================================
# GLOBAL CORE SCHEMAS & CONFIGURATION LOGISTICS PLATFORM MATRIX
# ==============================================================================

COLUMNS = [
    "Date", "Category", "Customer", "Agent", "HBL", "Liner", "Booking_MBL", 
    "Container", "POL", "POD", "ETD_as_per_SO", "ETD_ATD", "ETA_ATA", 
    "Follow_up_remarks", "Next_Follow_up", "HBL_Remarks", 
    "CFS_Nomination_De_Stuffing", "FC", "Revenue_to_be_Billed", 
    "Is_RFQ", "Deal_Finalized", "Revenue_yet_to_be_Billed",
    "Created_By", "Last_Updated_By", "Last_Modified_On",
    "Remarks", "Details", "Starttime", "Endtime", "Routing Key", "Email Link"
]

STAGES = [
    "Active RFQ",
    "Yet to sail",
    "On water",
    "Reached shore yet to release",
    "Released",
    "Empty container returned"
]

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
        "revenue": "Revenue_to_be_Billed", "rfq": "Is_RFQ", 
        "deal": "Deal_Finalized", "remarks": "Remarks", "details": "Details"
    }
