import streamlit as st
import pandas as pd
import requests
import json
import time
from utils import COLUMNS, STAGES

st.set_page_config(page_title="Log Shipment", layout="wide")

st.title("📥 Log New Sea Import Shipment")
st.caption("Type directly into the fields to select an existing name or create a brand-new entry instantly.")

PRODUCTION_URL = st.secrets["sheet_write_url"]
SPREADSHEET_ID = st.secrets["spreadsheet_id"]

def get_autocomplete_options():
    try:
        # Pulls directly from Google's internal engine bypassing apps script blocks entirely
        direct_csv_url = f"https://google.com{SPREADSHEET_ID}/export?format=csv&ts={int(time.time())}"
        df = pd.read_csv(direct_csv_url, dtype=str).fillna("")
        df.columns = df.columns.astype(str).str.strip()
        
        customers = sorted([c for c in df["Customer"].unique() if c.strip()]) if "Customer" in df.columns else []
        agents = sorted([a for a in df["Agent"].unique() if a.strip()]) if "Agent" in df.columns else []
        return customers, agents
    except:
        return [], []

existing_customers, existing_agents = get_autocomplete_options()

with st.form("new_shipment_form", clear_on_submit=True):
    r1_col1, r1_col2 = st.columns(2)
    with r1_col1:
        date_val = st.date_input("Nomination Tracking Date")
    with r1_col2:
        category_val = st.selectbox("Current Operational Phase", options=STAGES)
        
    st.markdown("---")
    r2_col1, r2_col2 = st.columns(2)
    
    with r2_col1:
        # SINGLE SEARCHABLE COMBINED TEXT BOX FOR CUSTOMERS
        customer_val = st.selectbox(
            "Customer Entity Title (Type to search / create new)",
            options=existing_customers if existing_customers else [""],
            index=0 if existing_customers else None,
            placeholder="Type or select customer name...",
            disabled=False
        )
        # Fallback to text input if list is empty so you are never locked out
        if not existing_customers:
            customer_val = st.text_input("Type Customer Name *")
            
    with r2_col2:
        # SINGLE SEARCHABLE COMBINED TEXT BOX FOR AGENTS
        agent_val = st.selectbox(
            "Assigned Agent Partner (Type to search / create new)",
            options=existing_agents if existing_agents else [""],
            index=0 if existing_agents else None,
            placeholder="Type or select agent partner..."
        )
        if not existing_agents:
            agent_val = st.text_input("Type Agent Name *")

    st.markdown("---")
    r3_col1, r3_col2, r3_col3, r3_col4 = st.columns(4)
    with r3_col1: liner_val = st.text_input("Liner Carrier / Vessel")
    with r3_col2: mbl_val = st.text_input("MBL / Booking Reference")
    with r3_col3: hbl_val = st.text_input("HBL Tracking ID")
    with r3_col4: container_val = st.text_input("Container Unit Code")
    
    st.markdown("---")
    r4_col1, r4_col2 = st.columns(2)
    with r4_col1: pol_val = st.text_input("POL (Port of Loading)")
    with r4_col2: pod_val = st.text_input("POD (Port of Discharge)")
    
    st.markdown("---")
    r5_col1, r5_col2, r5_col3 = st.columns(3)
    with r5_col1:
        etd_so_raw = st.date_input("ETD as per SO")
        check_etd_so = st.checkbox("Leave Blank", key="chk_etd_so")
    with r5_col2:
        etd_atd_raw = st.date_input("ETD / ATD")
        check_etd_atd = st.checkbox("Leave Blank", key="chk_etd_atd")
    with r5_col3:
        eta_ata_raw = st.date_input("ETA / ATA")
        check_eta_ata = st.checkbox("Leave Blank", key="chk_eta_ata")
        
    st.markdown("---")
    r6_col1, r6_col2 = st.columns(2)
    with r6_col1: remarks_val = st.text_area("Follow-up Remarks / Status Updates")
    with r6_col2:
        next_follow_raw = st.date_input("Next Follow-up Date")
        check_next = st.checkbox("Leave Blank", key="chk_next")
        
    st.markdown("---")
    r7_col1, r7_col2 = st.columns(2)
    with r7_col1: hbl_rem_val = st.text_area("HBL Remarks")
    with r7_col2: revenue_val = st.number_input("Revenue to be Billed (INR)", min_value=0.0, step=500.0)
    
    submit_btn = st.form_submit_button("🚀 Append File to Master Cloud Sheets Database", type="primary", use_container_width=True)
    
    if submit_btn:
        if not str(customer_val).strip() or not mbl_val.strip():
            st.error("⚠️ Required Fields Missing! Customer and MBL details must be populated.")
        else:
            payload = {col: "" for col in COLUMNS}
            payload["Date"] = str(date_val)
            payload["Category"] = str(category_val)
            payload["Customer"] = str(customer_val).strip()
            payload["Agent"] = str(agent_val).strip()
            payload["Liner"] = str(liner_val).strip()
            payload["Booking_MBL"] = str(mbl_val).strip()
            payload["HBL"] = str(hbl_val).strip()
            payload["Container"] = str(container_val).strip()
            payload["POL"] = str(pol_val).strip()
            payload["POD"] = str(pod_val).strip()
            
            payload["ETD_as_per_SO"] = "" if check_etd_so else str(etd_so_raw)
            payload["ETD_ATD"] = "" if check_etd_atd else str(etd_atd_raw)
            payload["ETA_ATA"] = "" if check_eta_ata else str(eta_ata_raw)
            payload["Next_Follow_up"] = "" if check_next else str(next_follow_raw)
            
            payload["Follow_up_remarks"] = str(remarks_val).strip()
            payload["HBL_Remarks"] = str(hbl_rem_val).strip()
            payload["Revenue_to_be_Billed"] = str(revenue_val)
            
            for col in COLUMNS:
                if "Must Arrive" in col or "/" in col or "Tracking" in col or "Certificate" in col or "Payment" in col or "Procurement" in col or "Preparation" in col or "Prep" in col:
                    payload[col] = "No"
                    
            try:
                response = requests.post(PRODUCTION_URL, data=json.dumps(payload), headers={"Content-Type": "application/json"}, timeout=15)
                if response.status_code == 200:
                    st.success(f"🎉 Success! Shipment appended seamlessly to Google Sheet Row!")
                    st.balloons()
                    time.sleep(1)
                    st.rerun()
                else:
                    st.error(f"Server Error: {response.status_code}")
            except Exception as ex:
                st.error(f"Network Error: {ex}")
