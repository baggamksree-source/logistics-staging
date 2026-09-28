import streamlit as st
import requests
import json
from datetime import datetime, date
from utils import COLUMNS, STAGES

st.set_page_config(page_title="Entry Portal", layout="wide")

if not st.session_state.get("security_cleared", False):
    st.error("🔒 Security Authentication Required. Please clear the Home Hub gatekeeper page first.")
    st.stop()

st.title("📥 Operational Entry Portal Grid")
st.caption("Log fresh active, nominated container files directly to the core logging infrastructure using precise calendar dates.")

user_email = st.session_state.get("user_identity", "unknown_user")
WRITE_URL = st.secrets["sheet_write_url"]

# All 12 dynamic milestone headers exactly as defined in the master spreadsheet layout
milestone_columns = [
    "Nomination Certificate Acceptance", "Carting / Cargo Gate-in Pass", 
    "Shipping Instructions (SI) Cut-off", "Draft HBL Approval Loop", 
    "Verified Gross Mass (VGM) Submission", "Form 13 / Export Customs Gate Open", 
    "On-Board Bill of Lading (OBL) Issuance", "Carrier Invoice Settlement Request", 
    "Pre-Alert & Manifest Filing", "Delivery Order (DO) Document Release", 
    "Import Customs Clearance Filing", "De-Stuffing Nomination & Return"
]

ALL_SYSTEM_COLUMNS = COLUMNS + milestone_columns

with st.form(key="isolated_form", clear_on_submit=True):
    st.subheader("📋 Nominated Shipment Information Matrix")
    c1, c2, c3, c_agent = st.columns(4)
    with c1: log_dt = st.date_input("Tracking File Date", date.today())
    with c2: cat = st.selectbox("Current Operational Phase", STAGES)
    with c3: cust = st.text_input("Customer Entity Title").strip()
    with c_agent: agent = st.text_input("Assigned Agent Partner").strip()

    c4, c5, c6, c7 = st.columns(4)
    with c4: liner = st.text_input("Liner Carrier / Vessel").strip()
    with c5: mbl = st.text_input("MBL / Booking Reference").strip()
    with c6: hbl = st.text_input("HBL Tracking ID").strip()
    with c7: cont = st.text_input("Container Unit Code").strip()

    st.markdown("---")
    st.subheader("📊 Financial Pipeline Indicators")
    revenue = st.text_input("Revenue to be Billed (Numeric formatting only)").strip()

    st.markdown("---")
    st.subheader("🌐 Transit Tracking Vector Points")
    c10, c11, c12 = st.columns(3)
    with c10: pol = st.text_input("POL (Port of Loading)").strip()
    with c11: pod = st.text_input("POD (Port of Discharge)").strip()
    with c12: nxt = st.text_input("Next Scheduled Action").strip()

    c13, c14, c15 = st.columns(3)
    with c13: etd_so_dt = st.date_input("ETD Estimated Schedule (SO Date)", date.today())
    with c14: etd_atd_dt = st.date_input("ETD / ATD Verified Departure Target", date.today())
    with c15: eta_ata_dt = st.date_input("ETA / ATA Destination Arrival Status", date.today())

    save_btn = st.form_submit_button(label="🚀 Append File to Master Cloud Sheets Database")

if save_btn and cust:
    # Build complete foundational tracking payload layout keys mapping
    payload = {
        "Date": log_dt.strftime("%Y-%m-%d"), 
        "Category": cat.strip(), 
        "Customer": cust, 
        "Agent": agent, 
        "HBL": hbl, 
        "Liner": liner, 
        "Booking_MBL": mbl, 
        "Container": cont, 
        "POL": pol, 
        "POD": pod, 
        "ETD_as_per_SO": etd_so_dt.strftime("%Y-%m-%d"), 
        "ETD_ATD": etd_atd_dt.strftime("%Y-%m-%d"), 
        "ETA_ATA": eta_ata_dt.strftime("%Y-%m-%d"), 
        "Follow_up_remarks": "", 
        "Next_Follow_up": nxt, 
        "HBL_Remarks": "", 
        "CFS_Nomination_De_Stuffing": "", 
        "FC": "",
        "Revenue_to_be_Billed": revenue, 
        "Is_RFQ": "No", 
        "Deal_Finalized": "Yes",
        "Revenue_yet_to_be_Billed": "", 
        "Created_By": user_email, 
        "Last_Updated_By": user_email, 
        "Last_Modified_On": datetime.now().strftime("%Y-%m-%d %H:%M")
    }
    
    # Initialize all 12 checkboxes to "No" (Pending) explicitly inside the sent data array
    for milestone_key in milestone_columns:
        payload[milestone_key] = "No"
        
    # Crucial Structure Fix: Order all 35 columns perfectly matching Row 1 of your spreadsheet
    ordered_payload = {col: str(payload.get(col, "")) for col in ALL_SYSTEM_COLUMNS}
    
    try:
        # Send raw JSON request safely over HTTPS
        response = requests.post(WRITE_URL, data=json.dumps(ordered_payload), headers={"Content-Type": "application/json"})
        
        # --- NEW PIPELINE DIAGNOSTIC RADAR ---
        if response.status_code == 200:
            st.success("🚀 SUCCESS! Connected to Google server. Row has been permanently injected into your spreadsheet!")
            st.balloons()
        else:
            st.error(f"❌ SERVER REJECTION ({response.status_code}): Google accepted the signal but blocked the write event.")
            st.warning(f"Server response notes: {response.text}")
            
    except Exception as err:
        st.error(f"📡 NETWORK BLOCKED: Your app could not connect to the Webhook URL. Details: {err}")
