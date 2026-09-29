import streamlit as st
import requests
import json
from datetime import datetime, date
from utils import COLUMNS, STAGES

st.set_page_config(page_title="Entry Portal", layout="wide")

if not st.session_state.get("security_cleared", False):
    st.error("🔒 Security Authentication Required."); st.stop()

st.title("📥 Operational Entry Portal Grid")

# ── FORCED CORPORATE PRODUCTION URL BYPASS ──
PRODUCTION_URL = "https://script.google.com/macros/s/AKfycbyQK3DJnLU4j1JHr5Xsfq0FATxMwRo8UWkret4UL_cj7buA1HqhJCdB2oR8KVkHOLhgug/exec"

milestone_columns = [
    "SO Must Arrive", "Container Pick Up / Stuffing / Handover",
    "BL Draft Checking & Approval", "BL Approval from Shipper and Consignee",
    "Follow-up of Container Back to Terminal", "Vessel ETD+ Tracking",
    "Enquiry of Pre-alert Docs + D/N on ETD + SOB Confirmation",
    "On Water ETA Tracking", "Freight Certificate", "Remittance to Overseas Agent",
    "IGM File + CFS Nomination", "Local Charges Invoice Checking and Payment",
    "DO Procurement", "Cost Sheet Preparation", "Customer Invoice Prep + Submission to Client"
]

ALL_SYSTEM_COLUMNS = COLUMNS

with st.form(key="isolated_form", clear_on_submit=True):
    c1, c2, c3, c_agent = st.columns(4)
    with c1: log_dt = st.date_input("Nomination Tracking Date", date.today())
    with c2: cat = st.selectbox("Current Operational Phase", STAGES)
    with c3: cust = st.text_input("Customer Entity Title").strip()
    with c_agent: agent = st.text_input("Assigned Agent Partner").strip()

    c4, c5, c6, c7 = st.columns(4)
    with c4: liner = st.text_input("Liner Carrier / Vessel").strip()
    with c5: mbl = st.text_input("MBL / Booking Reference").strip()
    with c6: hbl = st.text_input("HBL Tracking ID").strip()
    with c7: cont = st.text_input("Container Unit Code").strip()

    c10, c11 = st.columns(2)
    with c10: pol = st.text_input("POL (Port of Loading)").strip()
    with c11: pod = st.text_input("POD (Port of Discharge)").strip()

    c13, c14, c15 = st.columns(3)
    with c13: etd_so_dt = st.date_input("SO Scheduled Date", date.today())
    with c14: etd_atd_dt = st.date_input("ETD / ATD Actual Date", date.today())
    with c15: eta_ata_dt = st.date_input("ETA / ATA Target Date", date.today())

    save_btn = st.form_submit_button(label="🚀 Append File to Master Cloud Sheets Database")

if save_btn and cust:
    payload = {
        "Date": log_dt.strftime("%Y-%m-%d"), "Category": cat, "Customer": cust, "Agent": agent,
        "HBL": hbl, "Liner": liner, "Booking_MBL": mbl, "Container": cont, "POL": pol, "POD": pod,
        "ETD_as_per_SO": etd_so_dt.strftime("%Y-%m-%d"), "ETD_ATD": etd_atd_dt.strftime("%Y-%m-%d"),
        "ETA_ATA": eta_ata_dt.strftime("%Y-%m-%d"), "Created_By": "ops_team", "Last_Updated_By": "ops_team",
        "Last_Modified_On": datetime.now().strftime("%Y-%m-%d %H:%M")
    }
    
    for milestone_key in milestone_columns:
        payload[milestone_key] = "No"
        
    ordered_payload = {col: str(payload.get(col, "")) for col in ALL_SYSTEM_COLUMNS}
    
    try:
        response = requests.post(PRODUCTION_URL, data=json.dumps(ordered_payload), headers={"Content-Type": "application/json"})
        if response.status_code == 200:
            st.success("🚀 SUCCESS! Connected to Google server. Row has been permanently injected into your spreadsheet!")
        else:
            st.error(f"❌ SERVER REJECTION ({response.status_code})")
    except Exception as err:
        st.error(f"📡 NETWORK BLOCKED: {err}")
