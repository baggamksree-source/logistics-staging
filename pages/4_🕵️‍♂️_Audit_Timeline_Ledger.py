import streamlit as st
import pandas as pd
from datetime import datetime

st.set_page_config(page_title="Audit Trail Hub", layout="wide")

# Ensure user has logged into the main app gatekeeper page first
if not st.session_state.get("security_cleared", False):
    st.error("🔒 Security Authentication Required. Please clear the Home Hub gatekeeper page first.")
    st.stop()

st.title("🕵️‍♂️ Operational Audit Log Ledger")
st.caption("Review historical user footprints, row creation sources, and live editing tracking trails for active nominated files.")

READ_URL = st.secrets["sheet_read_url"]

def download_audit_logs():
    try:
        # Fetch directly from the master Google Sheet cloud stream
        raw_df = pd.read_csv(READ_URL, on_bad_lines='skip', dtype=str).fillna("")
        if not raw_df.empty:
            raw_df.columns = raw_df.columns.astype(str).str.strip()
            
            # Auto-repair columns if fields aren't initialized yet
            for meta_col in ["Created_By", "Last_Updated_By", "Last_Modified_On", "Booking_MBL", "HBL", "Customer"]:
                if meta_col not in raw_df.columns:
                    raw_df[meta_col] = "System Trace Missing"
                    
            return raw_df
    except Exception as error:
        st.sidebar.error(f"Audit engine connection error: {error}")
    return pd.DataFrame()

audit_master_df = download_audit_logs()

if audit_master_df.empty:
    st.info("The operational audit log ledger contains no transaction history yet.")
else:
    # Filter down specifically to core transaction trail columns
    display_cols = ["Booking_MBL", "HBL", "Customer", "Created_By", "Last_Updated_By", "Last_Modified_On"]
    refined_logs = audit_master_df[display_cols].copy()
    
    # Sort logs so the absolute newest edits float straight to the top
    refined_logs = refined_logs.sort_values(by="Last_Modified_On", ascending=False)
    
    # --- ADMIN FILTERING TOOL BAR ---
    st.markdown("### 🔍 Search & Filter Footprints")
    c1, c2 = st.columns(2)
    with c1:
        search_user = st.text_input("Filter by Operator Email / Name:").strip().lower()
    with c2:
        search_mbl = st.text_input("Filter by Booking / MBL Number:").strip().lower()
        
    if search_user:
        refined_logs = refined_logs[
            (refined_logs["Created_By"].astype(str).str.lower().str.contains(search_user)) | 
            (refined_logs["Last_Updated_By"].astype(str).str.lower().str.contains(search_user))
        ]
        
    if search_mbl:
        refined_logs = refined_logs[refined_logs["Booking_MBL"].astype(str).str.lower().str.contains(search_mbl)]
        
    # --- TIMELINE LEDGER GRID DISPLAY ---
    st.markdown("---")
    st.subheader("📋 System Modifications Footprint Log")
    
    st.dataframe(
        refined_logs,
        use_container_width=True,
        hide_index=True,
        column_config={
            "Booking_MBL": st.column_config.TextColumn("Booking / MBL"),
            "HBL": st.column_config.TextColumn("House HBL"),
            "Customer": st.column_config.TextColumn("Target Client"),
            "Created_By": st.column_config.TextColumn("Original File Creator"),
            "Last_Updated_By": st.column_config.TextColumn("Most Recent Modifier"),
            "Last_Modified_On": st.column_config.TextColumn("Timestamp of Modification")
        }
    )
    
    # --- INTERACTIVE EXPORT BUTTON ---
    st.markdown("---")
    csv_data = refined_logs.to_csv(index=False).encode('utf-8')
    st.download_button(
        label="📥 Download Certified Audit Logs to CSV",
        data=csv_data,
        file_name=f"Nominated_Shipments_Audit_Log_{datetime.now().strftime('%Y%m%d')}.csv",
        mime="text/csv"
    )
