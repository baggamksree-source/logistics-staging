import streamlit as st
import pandas as pd
import requests
import json
import time
from utils import COLUMNS, STAGES

st.set_page_config(page_title="Log Shipment", layout="wide")

st.title("📥 Log New Sea Import Shipment")
st.caption("Clean 1-box setup. Enter shipment lines freely. Only Customer field is mandatory.")

PRODUCTION_URL = st.secrets["sheet_write_url"]
SPREADSHEET_ID = st.secrets["spreadsheet_id"]

def get_autocomplete_options():
    try:
        direct_csv_url = f"https://google.com{SPREADSHEET_ID}/export?format=csv&ts={int(time.time())}"
        df = pd.read_csv(direct_csv_url, dtype=str).fillna("")
        df.columns = df.columns.astype(str).str.strip()
        
        customers = sorted([c for c in df["Customer"].unique() if str(c).strip()]) if "Customer" in df.columns else []
        agents = sorted([a for a in df["Agent"].unique() if str(a).strip()]) if "Agent" in df.columns else []
        pols = sorted([p for p in df["POL"].unique() if str(p).strip()]) if "POL" in df.columns else []
        pods = sorted([d for d in df["POD"].unique() if str(d).strip()]) if "POD" in df.columns else []
        return customers, agents, pols, pods
    except:
        return [], [], [], []

existing_customers, existing_agents, existing_pols, existing_pods = get_autocomplete_options()

with st.form("new_shipment_form", clear_on_submit=True):
    r1_col1, r1_col2 = st.columns(2)
    with r1_col1:
        date_val = st.date_input("Nomination Tracking Date")
    with r1_col2:
        category_val = st.selectbox("Current Operational Phase", options=STAGES)
        
    st.markdown("---")
    r2_col1, r2_col2 = st.columns(2)
    
    with r2_col1:
        # CLEANED: Single input box configuration for Customer entry field
        customer_val = st.text_input(
            "Customer Entity Title *", 
            value="", 
            placeholder="Type customer name... (Autocomplete reads: " + ", ".join(existing_customers[:3]) + ")" if existing_customers else "Type customer name..."
        )
            
    with r2_col2:
        # CLEANED: Single input box configuration for Agent entry field
        agent_val = st.text_input(
            "Assigned Agent Partner", 
            value="", 
            placeholder="Type agent name... (Autocomplete reads: " + ", ".join(existing_agents[:3]) + ")" if existing_agents else "Type agent name..."
        )

    st.markdown("---")
    r3_col1, r3_col2, r3_col3, r3_col4 = st.columns(4)
    with r3_col1: liner_val = st.text_input("Liner Carrier / Vessel")
    with r3_col2: mbl_val = st.text_input("MBL / Booking Reference (Optional)") # UNLOCKED
    with r3_col3: hbl_val = st.text_input("HBL Tracking ID")
    with r3_col4: container_val = st.text_input("Container Unit Code")
    
    st.markdown("---")
    r4_col1, r4_col2 = st.columns(2)
    with r4_col1: 
        pol_val = st.text_input(
            "POL (Port of Loading)", 
            value="", 
            placeholder="Type port... (Common: " + ", ".join(existing_pols[:2]) + ")" if existing_pols else "Type port..."
        )
    with r4_col2: 
        pod_val = st.text_input(
            "POD (Port of Discharge)", 
            value="", 
            placeholder="Type port... (Common: " + ", ".join(existing_pods[:2]) + ")" if existing_pods else "Type port..."
        )
    
    st.markdown("---")
    r5_col1, r5_col2, r5_col3 = st.columns(3)
    with r5_col1:
        etd_so_raw = st.date_input("ETD as per SO")
        check_etd_so = st.checkbox("Leave Blank", key="chk_etd_so", value=True)
    with r5_col2:
        etd_atd_raw = st.date_input("ETD / ATD")
        check_etd_atd = st.checkbox("Leave Blank", key="chk_etd_atd", value=True)
    with r5_col3:
        eta_ata_raw = st.date_input("ETA / ATA")
        check_eta_ata = st.checkbox("Leave Blank", key="chk_eta_ata", value=True)
        
    st.markdown("---")
    r6_col1, r6_col2 = st.columns(2)
    with r6_col1: remarks_val = st.text_area("Follow-up Remarks / Status Updates")
    with r6_col2:
        next_follow_raw = st.date_input("Next Follow-up Date")
        check_next = st.checkbox("Leave Blank", key="chk_next", value=True)
        
    st.markdown("---")
    r7_col1, r7_col2 = st.columns(2)
    with r7_col1: hbl_rem_val = st.text_area("HBL Remarks")
    with r7_col2: revenue_val = st.number_input("Revenue to be Billed (INR)", min_value=0.0, step=500.0)
    
    submit_btn = st.form_submit_button("🚀 Append File to Master Cloud Sheets Database", type="primary", use_container_width=True)
    
    if submit_btn:
        # VALIDATION UNLOCKED: Only customer name validation check remains active
        if not str(customer_val).strip():
            st.error("⚠️ Required Fields Missing! Customer field must be populated.")
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
                if any(phrase in col for phrase in ["Must Arrive", "/", "Tracking", "Certificate", "Payment", "Procurement", "Preparation", "Prep"]):
                    payload[col] = "No"
                    
            try:
                response = requests.post(PRODUCTION_URL, data=json.dumps(payload), headers={"Content-Type": "application/json"}, timeout=15)
                if response.status_code == 200:
                    st.success(f"🎉 Success! Shipment line for '{customer_val}' appended seamlessly!")
                    st.balloons()
                    time.sleep(1)
                    st.rerun()
                else:
                    st.error(f"Server Error: {response.status_code}")
            except Exception as ex:
                st.error(f"Network Error: {ex}")
