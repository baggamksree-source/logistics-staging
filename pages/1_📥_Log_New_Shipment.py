import streamlit as st
import requests
import json
from datetime import datetime
from utils import COLUMNS, STAGES, DOCS

st.set_page_config(page_title="Entry Portal", layout="wide")

if not st.session_state.get("security_cleared", False):
    st.error("🔒 Security Authentication Required. Please clear the Home Hub gatekeeper page first."); st.stop()

st.title("📥 Operational Entry Portal Grid")
user_email = st.session_state.get("user_identity", "unknown_user")
WRITE_URL = st.secrets["sheet_write_url"]

with st.form(key="isolated_form", clear_on_submit=True):
    st.subheader("📋 Core Shipment Information Matrix")
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
    c8, c9 = st.columns(2)
    with c8: revenue = st.text_input("Revenue to be Billed (Numeric formatting only)").strip()
    with c9:
        st.write("System Parameter Flags:")
        is_rfq = st.checkbox("Mark as Active Price Query (RFQ)", value=(cat == "Active RFQ"))
        is_deal = st.checkbox("Mark Asset as Closed/Finalized Deal")

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

    st.markdown("---")
    st.caption("📝 Optional Custom RFQ Parameters")
    rc1, rc2 = st.columns(2)
    with rc1: rfq_rem = st.text_input("Pricing Core Remarks").strip()
    with rc2: rfq_det = st.text_area("Detailed Cargo Specs").strip()

    rc3, rc4, rc5, rc6 = st.columns(4)
    with rc3: rfq_start = st.text_input("Start Time Window").strip()
    with rc4: rfq_end = st.text_input("End Time Window").strip()
    with rc5: rfq_rkey = st.text_input("Routing Pipeline Key").strip()
    with rc6: rfq_link = st.text_input("Email Reference URL Link").strip()

    save_btn = st.form_submit_button(label="🚀 Append File to Master Cloud Sheets Database")

if save_btn and cust:
    payload = {
        "Date": log_dt.strftime("%Y-%m-%d"), "Category": cat.strip(), "Customer": cust, "Agent": "", 
        "HBL": hbl, "Liner": liner, "Booking_MBL": mbl, "Container": cont, "POL": pol, "POD": pod, 
        "ETD_as_per_SO": etd_so, "ETD_ATD": etd_atd, "ETA_ATA": eta_ata, "Follow_up_remarks": "", 
        "Next_Follow_up": nxt, "HBL_Remarks": "", "CFS_Nomination_De_Stuffing": "", "FC": "",
        "Revenue_to_be_Billed": revenue, "Is_RFQ": "Yes" if (is_rfq or cat == "Active RFQ") else "No", "Deal_Finalized": "Yes" if is_deal else "No",
        "Revenue_yet_to_be_Billed": "", "Created_By": user_email, "Last_Updated_By": user_email, "Last_Modified_On": datetime.now().strftime("%Y-%m-%d %H:%M"),
        "Remarks": rfq_rem, "Details": rfq_det, "Starttime": rfq_start, "Endtime": rfq_end, "Routing Key": rfq_rkey, "Email Link": rfq_link
    }
    for doc in DOCS.keys(): payload[doc] = "No"
    ordered_payload = {col: payload.get(col, "No" if col in DOCS.keys() else "") for col in COLUMNS}
    
    try:
        requests.post(WRITE_URL, data=json.dumps(ordered_payload))
        st.success("✓ Entry dynamically saved to cloud masters matrix spreadsheet layout!")
    except Exception as err:
        st.error(f"Network error trying to contact Google server hook: {err}")
