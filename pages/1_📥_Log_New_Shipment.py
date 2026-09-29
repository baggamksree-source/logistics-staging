import streamlit as st
import requests
import json
import pandas as pd
from datetime import datetime, date
from utils import COLUMNS, STAGES

st.set_page_config(page_title="Entry Portal", layout="wide")

if not st.session_state.get("security_cleared", False):
    st.error("🔒 Security Authentication Required. Go to Home Hub page first."); st.stop()

st.title("📥 Operational Entry Portal Grid")
st.caption("Log fresh nominated container files. Repetitive fields autocomplete automatically based on historical rows data.")

# ── INSERT YOUR NEW COPIED OFFICE ID DEPLOYMENT LINK HERE ──
PRODUCTION_URL = "https://script.google.com/macros/s/AKfycbxP9HmhKhRW6X6VAEOI9IWp9bc5DY8RbfqAMTYLIN3wGX-EKNnuup-kNucPZ-jtL7sTSg/exec"

milestone_columns = [
    "SO Must Arrive", "Container Pick Up / Stuffing / Handover",
    "BL Draft Checking & Approval", "BL Approval from Shipper and Consignee",
    "Follow-up of Container Back to Terminal", "Vessel ETD+ Tracking",
    "Enquiry of Pre-alert Docs + D/N on ETD + SOB Confirmation",
    "On Water ETA Tracking", "Freight Certificate", "Remittance to Overseas Agent",
    "IGM File + CFS Nomination", "Local Charges Invoice Checking and Payment",
    "DO Procurement", "Cost Sheet Preparation", "Customer Invoice Prep + Submission to Client"
]

@st.cache_data(ttl=60)
def fetch_autocomplete_lists():
    try:
        df = pd.read_csv(PRODUCTION_URL, dtype=str).fillna("")
        df.columns = df.columns.astype(str).str.strip()
        return {
            "cust": sorted(list(set(df["Customer"].dropna().str.strip()))),
            "agent": sorted(list(set(df["Agent"].dropna().str.strip()))),
            "pol": sorted(list(set(df["POL"].dropna().str.strip()))),
            "pod": sorted(list(set(df["POD"].dropna().str.strip())))
        }
    except:
        return {"cust":[], "agent":[], "pol":[], "pod":[]}

history = fetch_autocomplete_lists()

with st.form(key="isolated_form", clear_on_submit=True):
    st.subheader("📋 Nominated Shipment Information Matrix")
    
    c1, c2 = st.columns(2)
    with c1: log_dt = st.date_input("Nomination Tracking Date", date.today())
    with c2: cat = st.selectbox("Current Operational Phase", STAGES)
        
    col_cust, col_ag = st.columns(2)
    with col_cust:
        cust = st.selectbox("Customer Entity Title (Type to search / fill)", [""] + history["cust"] + ["-- New Customer --"])
        if cust == "-- New Customer --" or not history["cust"]:
            cust = st.text_input("Enter New Customer Name").strip()
    with col_ag:
        agent = st.selectbox("Assigned Agent Partner (Type to search / fill)", [""] + history["agent"] + ["-- New Agent --"])
        if agent == "-- New Agent --" or not history["agent"]:
            agent = st.text_input("Enter New Agent Partner Name").strip()

    c4, c5, c6, c7 = st.columns(4)
    with c4: liner = st.text_input("Liner Carrier / Vessel").strip()
    with c5: mbl = st.text_input("MBL / Booking Reference").strip()
    with c6: hbl = st.text_input("HBL Tracking ID").strip()
    with c7: cont = st.text_input("Container Unit Code").strip()

    st.markdown("---")
    st.subheader("🌐 Transit Tracking Vector Points & Smart Pickers")
    
    c_pol, c_pod = st.columns(2)
    with c_pol:
        pol = st.selectbox("POL (Port of Loading)", [""] + history["pol"] + ["-- New POL --"])
        if pol == "-- New POL --" or not history["pol"]:
            pol = st.text_input("Enter New POL Text").strip()
    with c_pod:
        pod = st.selectbox("POD (Port of Discharge)", [""] + history["pod"] + ["-- New POD --"])
        if pod == "-- New POD --" or not history["pod"]:
            pod = st.text_input("Enter New POD Text").strip()

    st.markdown("##### 📅 Operational Date Matrix (Check 'Leave Blank' if unavailable yet)")
    
    d1, d1_chk, d2, d2_chk, d3, d3_chk = st.columns(6)
    with d1: etd_so_dt = st.date_input("SO Scheduled Date", date.today())
    with d1_chk: so_blank = st.checkbox("Leave Blank", key="so_b")
    
    with d2: etd_atd_dt = st.date_input("ETD / ATD Actual Date", date.today())
    with d2_chk: atd_blank = st.checkbox("Leave Blank", key="atd_b")
    
    with d3: eta_ata_dt = st.date_input("ETA / ATA Target Date", date.today())
    with d3_chk: eta_blank = st.checkbox("Leave Blank", key="eta_b")

    st.markdown("---")
    st.subheader("💰 Financial Parameters")
    revenue = st.text_input("Revenue to be Billed (Amount)").strip()

    save_btn = st.form_submit_button(label="🚀 Append File to Master Cloud Sheets Database")

if save_btn and cust:
    payload = {
        "Date": log_dt.strftime("%Y-%m-%d"), "Category": cat, "Customer": str(cust).strip(), "Agent": str(agent).strip(),
        "HBL": hbl, "Liner": liner, "Booking_MBL": mbl, "Container": cont, "POL": str(pol).strip(), "POD": str(pod).strip(),
        "ETD_as_per_SO": "" if so_blank else etd_so_dt.strftime("%Y-%m-%d"), 
        "ETD_ATD": "" if atd_blank else etd_atd_dt.strftime("%Y-%m-%d"),
        "ETA_ATA": "" if eta_blank else eta_ata_dt.strftime("%Y-%m-%d"), 
        "Follow_up_remarks": "", "Next_Follow_up": "", "HBL_Remarks": "", 
        "Revenue_to_be_Billed": revenue
    }
    for m_key in milestone_columns:
        payload[m_key] = "No"
        
    ordered_payload = {col: str(payload.get(col, "")) for col in COLUMNS}
    
    try:
        response = requests.post(PRODUCTION_URL, data=json.dumps(ordered_payload), headers={"Content-Type": "application/json"})
        st.success("🚀 SUCCESS! Row has been permanently injected into your spreadsheet tab!")
        st.cache_data.clear()
    except Exception as err:
        st.error(f"📡 CONNECTION FAILED: {err}")
