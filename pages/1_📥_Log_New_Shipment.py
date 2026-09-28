import streamlit as st
import requests
import json
from datetime import datetime
from utils import COLUMNS, STAGES

st.set_page_config(page_title="Entry Portal", layout="wide")

if not st.session_state.get("security_cleared", False):
    st.error("🔒 Security Authentication Required. Please clear the Home Hub gatekeeper page first.")
    st.stop()

st.title("📥 Operational Entry Portal Grid")
st.caption("Log fresh active, nominated container files directly to the core logging infrastructure.")

user_email = st.session_state.get("user_identity", "unknown_user")
WRITE_URL = st.secrets["sheet_write_url"]

with st.form(key="isolated_form", clear_on_submit=True):
    st.subheader("📋 Nominated Shipment Information Matrix")
    c1, c2, c3 = st.columns(3)
    with c1: log_dt = st.date_input("Tracking File Date", datetime.today())
    with c2: cat = st.selectbox("Current Operational Phase", STAGES)
    with c3: cust = st.text_input("Customer Entity Title").strip()

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
    with c13: etd_so = st.text_input("ETD Estimated Schedule").strip()
    with c14: etd_atd = st.text_input("ETD/ATD Verified Target").strip()
    with c15: eta_ata = st.text_input("ETA/ATA Status Matrix").strip()

    save_btn = st.form_submit_button(label="🚀 Append File to Master Cloud Sheets Database")

if save_btn and cust:
    payload = {
        "Date": log_dt.strftime("%Y-%m-%d"), "Category": cat.strip(), "Customer": cust, "Agent": "", 
        "HBL": hbl, "Liner": liner, "Booking_MBL": mbl, "Container": cont, "POL": pol, "POD": pod, 
        "ETD_as_per_SO": etd_so, "ETD_ATD": etd_atd, "ETA_ATA": eta_ata, "Follow_up_remarks": "", 
        "Next_Follow_up": nxt, "HBL_Remarks": "", "CFS_Nomination_De_Stuffing": "", "FC": "",
        "Revenue_to_be_Billed": revenue, "Is_RFQ": "No", "Deal_Finalized": "Yes",
        "Revenue_yet_to_be_Billed": "", "Created_By": user_email, "Last_Updated_By": user_email, "Last_Modified_On": datetime.now().strftime("%Y-%m-%d %H:%M")
    }
    
    # Static fallback array lists to perfectly initialize tracking data fields safely
    milestone_columns = [
        "Nomination Certificate Acceptance", "Carting / Cargo Gate-in Pass", 
        "Shipping Instructions (SI) Cut-off", "Draft HBL Approval Loop", 
        "Verified Gross Mass (VGM) Submission", "Form 13 / Export Customs Gate Open", 
        "On-Board Bill of Lading (OBL) Issuance", "Carrier Invoice Settlement Request", 
        "Pre-Alert & Manifest Filing", "Delivery Order (DO) Document Release", 
        "Import Customs Clearance Filing", "De-Stuffing Nomination & Return"
    ]
    for milestone_key in milestone_columns:
        payload[milestone_key] = "No"
        
    ordered_payload = {col: payload.get(col, "") for col in COLUMNS + milestone_columns}
    
    try:
        requests.post(WRITE_URL, data=json.dumps(ordered_payload))
        st.success("✓ Nominated file dynamically saved to cloud masters matrix spreadsheet layout!")
    except Exception as err:
        st.error(f"Network error trying to contact Google server hook: {err}")
