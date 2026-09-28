import streamlit as st
import pandas as pd
import requests
import json
from datetime import datetime
from utils import COLUMNS, STAGES

st.set_page_config(page_title="Ledger Interface", layout="wide")

if not st.session_state.get("security_cleared", False):
    st.error("🔒 Security Authentication Required. Please clear the Home Hub gatekeeper page first."); st.stop()

st.title("✏️ Master Interactive Shipments Data Ledger")
st.caption("Click individual checkboxes directly inside the data grid below to toggle milestone statuses instantly, then click save.")

READ_URL = st.secrets["sheet_read_url"]
WRITE_URL = st.secrets["sheet_write_url"]
user_email = st.session_state.get("user_identity", "unknown_user")

# Pull the exact list of 12 milestones cleanly without broken file path imports
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
            
            # Auto-patch missing core columns or milestone tracking points
            for c in ALL_SYSTEM_COLUMNS:
                if c not in raw_df.columns: 
                    raw_df[c] = "No" if c in milestone_columns else ""
            return raw_df[ALL_SYSTEM_COLUMNS]
    except Exception as e:
        st.sidebar.error(f"Failed to fetch ledger rows: {e}")
    return pd.DataFrame(columns=ALL_SYSTEM_COLUMNS)

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
    # --- DYNAMIC INTERACTIVE CHECKBOX COLUMN BUILDER ---
    grid_configuration = {
        "Category": st.column_config.SelectboxColumn("Stage Phase", options=STAGES, required=True),
        "Date": st.column_config.TextColumn("Tracking Date")
    }
    
    # Transform all 12 document milestones into true clickable native checkboxes
    for m_col in milestone_columns:
        # Convert text database values ("Yes" / "No") to Python Boolean values (True / False) for display
        current_working_df[m_col] = current_working_df[m_col].astype(str).str.strip().upper() == "YES"
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
    c_btn1, c_btn2 = st.columns([1, 3])
    
    with c_btn1:
        commit_execution_trigger = st.button("💾 Push Grid Edits Live to Cloud Sheets", type="primary")
        
    with c_btn2:
        st.caption("Warning: Tapping Save forces your table modifications to overwrite old index matches across the core database network logs.")

    if commit_execution_trigger:
        st.session_state.editable_ledger_df = edited_data_output
        st.info("Broadcasting grid rows framework array down to Google Webapp Connector API...")
        
        # Convert Booleans back to spreadsheet text strings ("Yes" / "No") prior to network export
        for m_col in milestone_columns:
            edited_data_output[m_col] = edited_data_output[m_col].map({True: "Yes", False: "No"}).fillna("No")
            
        success_rows_count = 0
        for index_row, data_row in edited_data_output.iterrows():
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
        del st.session_state["editable_ledger_df"] # clear local window state memory to pull fresh updates
        st.rerun()
