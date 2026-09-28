import streamlit as st
import pandas as pd
import requests
import json
from datetime import datetime
from utils import COLUMNS, STAGES

st.set_page_config(page_title="Ledger Interface", layout="wide")

if not st.session_state.get("security_cleared", False):
    st.error("🔒 Security Authentication Required. Please clear the Home Hub gatekeeper page first.")
    st.stop()

st.title("✏️ Master Interactive Shipments Data Ledger")
st.caption("Click individual checkboxes directly inside the data grid below to toggle milestone statuses instantly, then click save.")

READ_URL = st.secrets["sheet_read_url"]
WRITE_URL = st.secrets["sheet_write_url"]
user_email = st.session_state.get("user_identity", "unknown_user")

# Complete tracking checklist array list definitions 
milestone_columns = [
    "Nomination Certificate Acceptance", "Carting / Cargo Gate-in Pass", 
    "Shipping Instructions (SI) Cut-off", "Draft HBL Approval Loop", 
    "Verified Gross Mass (VGM) Submission", "Form 13 / Export Customs Gate Open", 
    "On-Board Bill of Lading (OBL) Issuance", "Carrier Invoice Settlement Request", 
    "Pre-Alert & Manifest Filing", "Delivery Order (DO) Document Release", 
    "Import Customs Clearance Filing", "De-Stuffing Nomination & Return"
]

ALL_SYSTEM_COLUMNS = COLUMNS + milestone_columns

def download_raw_cloud_rows():
    try:
        cb_url = f"{READ_URL}&t={int(datetime.now().timestamp())}" if "?" in READ_URL else f"{READ_URL}?t={int(datetime.now().timestamp())}"
        raw_df = pd.read_csv(cb_url, on_bad_lines='skip', dtype=str).fillna("")
        if not raw_df.empty:
            raw_df.columns = raw_df.columns.astype(str).str.strip()
            # Ensure every column from our schema exists in the data frame cleanly
            for c in ALL_SYSTEM_COLUMNS:
                if c not in raw_df.columns: 
                    raw_df[c] = "No"
            return raw_df[ALL_SYSTEM_COLUMNS]
    except Exception as e:
        st.sidebar.error(f"Failed to fetch ledger rows: {e}")
    
    # Solid fallback builder: Creates clean empty structural tracking row grids if spreadsheet data is blank
    blank_df = pd.DataFrame(columns=ALL_SYSTEM_COLUMNS)
    return blank_df

# Handle memory tracking states across frame sessions safely
if "editable_ledger_df" not in st.session_state:
    st.session_state.editable_ledger_df = download_raw_cloud_rows()

if st.sidebar.button("🔄 Discard Changes & Force Re-Sync"):
    if "editable_ledger_df" in st.session_state:
        del st.session_state.editable_ledger_df
    st.session_state.editable_ledger_df = download_raw_cloud_rows()
    st.rerun()

# Deep copy to break any underlying Pandas data references completely
current_working_df = st.session_state.editable_ledger_df.copy()

# Ensure database columns exist safely prior to running column adjustments using explicit indexing
for col in ALL_SYSTEM_COLUMNS:
    if col not in current_working_df.columns:
        current_working_df[col] = "No"

# --- DYNAMIC INTERACTIVE CHECKBOX COLUMN BUILDER ---
grid_configuration = {
    "Category": st.column_config.SelectboxColumn("Stage Phase", options=STAGES, required=True),
    "Date": st.column_config.TextColumn("Tracking Date")
}

# Convert text database formatting to pure Python boolean true/false checkboxes safely
for m_col in milestone_columns:
    # Safe structural transformation using data series mapping
    series_data = current_working_df[m_col].fillna("No").astype(str).str.strip().str.upper()
    current_working_df[m_col] = series_data.map({"YES": True, "NO": False}).fillna(False)
    grid_configuration[m_col] = st.column_config.CheckboxColumn(m_col, default=False)

# ── ADVANCED INTERACTIVE DATA MATRIX GRID VIEW ──
edited_data_output = st.data_editor(
    current_working_df,
    use_container_width=True,
    hide_index=False,
    num_rows="dynamic",
    column_config=grid_configuration
)

st.markdown("---")
st.subheader("💾 Database Commit Control Matrix")
c_btn1, c_btn2 = st.columns(2)

with c_btn1:
    commit_execution_trigger = st.button("💾 Push Grid Edits Live to Cloud Sheets", type="primary")
    
with c_btn2:
    st.caption("Warning: Tapping Save forces your table modifications to overwrite old index matches across the core database network logs.")

if commit_execution_trigger:
    st.info("Broadcasting grid rows framework array down to Google Webapp Connector API...")
    
    # Process modifications output cleanly back into spreadsheet string variables
    final_sync_df = edited_data_output.copy()
    for m_col in milestone_columns:
        final_sync_df[m_col] = final_sync_df[m_col].map({True: "Yes", False: "No"}).fillna("No")
        
    success_rows_count = 0
    
    if not final_sync_df.empty:
        for index_row, data_row in final_sync_df.iterrows():
            dict_payload = data_row.to_dict()
            dict_payload["Last_Updated_By"] = user_email
            dict_payload["Last_Modified_On"] = datetime.now().strftime("%Y-%m-%d %H:%M")
            
            payload_ordered = {col: str(dict_payload.get(col, "")) for col in ALL_SYSTEM_COLUMNS}
            try:
                requests.post(WRITE_URL, data=json.dumps(payload_ordered))
                success_rows_count += 1
            except:
                pass
            
    st.success(f"✓ Success! Synchronized matrix array processed. ({success_rows_count} entries verified and mapped).")
    st.cache_data.clear()
    if "editable_ledger_df" in st.session_state:
        del st.session_state["editable_ledger_df"]
    st.rerun()
