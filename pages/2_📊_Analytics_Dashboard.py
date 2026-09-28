import streamlit as st
import pandas as pd
from datetime import datetime
from utils import COLUMNS

st.set_page_config(page_title="Executive Insights", layout="wide")

if not st.session_state.get("security_cleared", False):
    st.error("🔒 Security Authentication Required. Please clear the Home Hub gatekeeper page first."); st.stop()

st.title("📊 Volume Indicators & Financial Metric Analytics")
READ_URL = st.secrets["sheet_read_url"]

@st.cache_data(ttl=5)
def pull_live_metrics_stream():
    cb_url = f"{READ_URL}&t={int(datetime.now().timestamp())}" if "?" in READ_URL else f"{READ_URL}?t={int(datetime.now().timestamp())}"
    raw_df = pd.read_csv(cb_url, on_bad_lines='skip', dtype=str).fillna("")
    if not raw_df.empty:
        raw_df.columns = raw_df.columns.astype(str).str.strip()
        for col_name in COLUMNS:
            if col_name not in raw_df.columns: raw_df[col_name] = ""
        return raw_df[COLUMNS]
    return pd.DataFrame(columns=COLUMNS)

if st.sidebar.button("🔄 Clear Visual Cache Locks"):
    st.cache_data.clear()

master_df = pull_live_metrics_stream()

if master_df.empty:
    st.info("Logistics analytics metric stream is currently empty.")
else:
    master_df['Parsed_Date'] = pd.to_datetime(master_df['Date'], errors='coerce')
    wk_df = master_df[master_df['Parsed_Date'] >= (datetime.today() - pd.Timedelta(days=7))]
    mo_df = master_df[master_df['Parsed_Date'] >= (datetime.today() - pd.Timedelta(days=30))]
    
    num_rfqs = len(wk_df[(wk_df["Is_RFQ"].astype(str).str.strip() == "Yes") | (wk_df["Category"].astype(str).str.strip() == "Active RFQ")])
    actual_shipments = len(wk_df[(wk_df["Is_RFQ"].astype(str).str.strip() != "Yes") & (wk_df["Category"].astype(str).str.strip() != "Active RFQ")])
    num_deals = len(wk_df[wk_df["Deal_Finalized"].astype(str).str.strip() == "Yes"])
    
    def calculate_rev(dataframe_target):
        return pd.to_numeric(dataframe_target['Revenue_to_be_Billed'].astype(str).str.replace(r'[\$,]', '', regex=True), errors='coerce').fillna(0).sum()

    st.markdown("### 📈 Weekly Performance Status Overview")
    mc1, mc2, mc3 = st.columns(3)
    with mc1:
        st.markdown(f"<div style='background-color:#e8f4fd;padding:20px;border-radius:10px;border-left:6px solid #2196f3;'><h4 style='color:#0d47a1;margin:0;'>📦 Active Shipments Logged</h4><h2 style='color:#0d47a1;margin:10px 0 0 0;'>{actual_shipments} Lines</h2></div>", unsafe_allow_html=True)
    with mc2:
        st.markdown(f"<div style='background-color:#fff8e1;padding:20px;border-radius:10px;border-left:6px solid #ffb300;'><h4 style='color:#5d4037;margin:0;'>💬 Price Enquiries (RFQs)</h4><h2 style='color:#5d4037;margin:10px 0 0 0;'>{num_rfqs} Units</h2></div>", unsafe_allow_html=True)
    with mc3:
        st.markdown(f"<div style='background-color:#e8f5e9;padding:20px;border-radius:10px;border-left:6px solid #4caf50;'><h4 style='color:#1b5e20;margin:0;'>🤝 Closed/Finalized Deals</h4><h2 style='color:#1b5e20;margin:10px 0 0 0;'>{num_deals} Rows</h2></div>", unsafe_allow_html=True)

    st.markdown("---")
    st.markdown("### 💰 Financial Pipeline Invoicing Summary")
    fc1, fc2 = st.columns(2)
    with fc1:
        st.markdown(f"<div style='background-color:#f3e5f5;padding:25px;border-radius:12px;text-align:center;'><h3 style='color:#4a148c;margin:0;'>Rolling 7-Day Revenue</h3><h1 style='color:#4a148c;margin:15px 0 0 0;'>${calculate_rev(wk_df):,.2f}</h1></div>", unsafe_allow_html=True)
    with fc2:
        st.markdown(f"<div style='background-color:#efebe9;padding:25px;border-radius:12px;text-align:center;'><h3 style='color:#3e2723;margin:0;'>Rolling 30-Day Revenue</h3><h1 style='color:#3e2723;margin:15px 0 0 0;'>${calculate_rev(mo_df):,.2f}</h1></div>", unsafe_allow_html=True)
