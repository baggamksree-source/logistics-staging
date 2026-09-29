# ==============================================================================
# GLOBAL CORE SCHEMAS & CONFIGURATION LOGISTICS PLATFORM MATRIX
# ==============================================================================

COLUMNS = [
    "Date", "Category", "Customer", "Agent", "HBL", "Liner", "Booking_MBL", 
    "Container", "POL", "POD", "ETD_as_per_SO", "ETD_ATD", "ETA_ATA", 
    "Follow_up_remarks", "Next_Follow_up", "HBL_Remarks", 
    "CFS_Nomination_De_Stuffing", "FC", "Revenue_to_be_Billed", 
    "Revenue_yet_to_be_Billed", "Created_By", "Last_Updated_By", "Last_Modified_On",
    "SO Must Arrive", "Container Pick Up / Stuffing / Handover",
    "BL Draft Checking & Approval", "BL Approval from Shipper and Consignee",
    "Follow-up of Container Back to Terminal", "Vessel ETD+ Tracking",
    "Enquiry of Pre-alert Docs + D/N on ETD + SOB Confirmation",
    "On Water ETA Tracking", "Freight Certificate", "Remittance to Overseas Agent",
    "IGM File + CFS Nomination", "Local Charges Invoice Checking and Payment",
    "DO Procurement", "Cost Sheet Preparation", "Customer Invoice Prep + Submission to Client"
]

STAGES = [
    "Nominated",
    "Yet to sail",
    "On water",
    "Reached shore yet to release",
    "Released",
    "Empty container returned"
]
