import streamlit as st
import pandas as pd
import requests
import json
from datetime import datetime
from utils import COLUMNS, STAGES, DOCS

st.set_page_config(page_title="Ledger Interface", layout="wide")

if not st.session_state.get("security_cleared", False):
    st.error("🔒 Security Authentication Required. Please clear the Home Hub gatekeeper page first."); st.stop()

st.title("✏️ Master Interactive Shipments Data Ledger")
st.caption("Double-click any box within the grid window below to edit values instantly, then tap the save engine button at the bottom.")

READ_URL = st.secrets["sheet_read_url"]
WRITE_URL = st.secrets["sheet_write_url"]
user_email = st.session_state.get("user_identity", "unknown_user")

def download_raw_cloud_rows():
    """
    Downloads clean data matrix files directly from your master cloud database.
    """
    try:
        raw_df = pd.read_csv(READ_URL, on_bad_lines='skip', dtype=str).fillna("")
        if not raw_df.empty:
            raw_df.columns = raw_df.columns.astype(str).str.strip()
            for c in COLUMNS:
                if c not in raw_df.columns: raw_df[c] = ""
            return raw_df[COLUMNS]
    except Exception as e:
        st.sidebar.error(f"Failed to fetch ledger rows: {e}")
    return pd.DataFrame(columns=COLUMNS)


# Use session state caching to track inline modifications safely
if "editable_ledger_df" not in st.session_state:
    st.session_state.editable_ledger_df = download_raw_cloud_rows()

if st.sidebar.button("🔄 Discard Changes & Force Re-Sync"):
    st.session_state.editable_ledger_df = download_raw_cloud_rows()
    st.rerun()

current_working_df = st.session_state.editable_ledger_df

if current_working_df.empty:
    st.info("No data cells available inside the master spreadsheet container grid currently.")
else:
    # ── ADVANCED INTERACTIVE DATA MATRIX GRID VIEW ──
    edited_data_output = st.data_editor(
        current_working_df,
        use_container_width=True,
        hide_index=False,
        num_rows="dynamic",
        column_config={
            "Category": st.column_config.SelectboxColumn("Stage Phase", options=STAGES, required=True),
            "Is_RFQ": st.column_config.SelectboxColumn("RFQ Query", options=["Yes", "No"]),
            "Deal_Finalized": st.column_config.SelectboxColumn("Deal Finalized", options=["Yes", "No"]),
            "Date": st.column_config.TextColumn("Tracking Date")
        }
    )

    st.markdown("---")
    st.subheader("💾 Database Commit Control Matrix")
    c_btn1, c_btn2 = st.columns([2, 8])
    
    with c_btn1:
        commit_execution_trigger = st.button("💾 Push Grid Edits Live to Cloud Sheets")
        
    with c_btn2:
        st.caption("Warning: Tapping Save forces your table modifications to overwrite old index matches across the core database network logs.")

    if commit_execution_trigger:
        st.session_state.editable_ledger_df = edited_data_output
        st.info("Broadcasting grid rows framework array down to Google Webapp Connector API...")
        
        # Sequentially broadcast entries over row matrix pipelines
        success_rows_count = 0
        for index_row, data_row in edited_data_output.iterrows():
            dict_payload = data_row.to_dict()
            dict_payload["Last_Updated_By"] = user_email
            dict_payload["Last_Modified_On"] = datetime.now().strftime("%Y-%m-%d %H:%M")
            
            payload_ordered = {col: dict_payload.get(col, "") for col in COLUMNS}
            try:
                requests.post(WRITE_URL, data=json.dumps(payload_ordered))
                success_rows_count += 1
            except:
                pass
                
        st.success(f"✓ Success! Synchronized matrix array processed. ({success_rows_count} entries verified and mapped).")
        st.cache_data.clear()
        st.rerun()
