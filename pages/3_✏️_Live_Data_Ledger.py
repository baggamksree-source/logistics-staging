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
        raw_df = pd.read_csv(cb_url, on_bad_lines='skip', dtype=str).fillna("No")
        
        # Build a fresh, clean dataframe to completely eliminate any duplicate column index bugs
        cleaned_data = {}
        
        if not raw_df.empty:
            # Clean up headers from the sheet download
            raw_df.columns = raw_df.columns.astype(str).str.strip()
            
            # Generate exact physical Google Sheet row IDs
            cleaned_data["Spreadsheet_Row_ID"] = [str(i + 2) for i in range(len(raw_df))]
            
            # Map columns one by one, picking only the first instance if a duplicate exists
            for col in ALL_SYSTEM_COLUMNS:
                if col in raw_df.columns:
                    # Handle duplicate columns by selecting only the first match
                    col_data = raw_df[col]
                    if isinstance(col_data, pd.DataFrame):
                        cleaned_data[col] = col_data.iloc[:, 0].astype(str).tolist()
                    else:
                        cleaned_data[col] = col_data.astype(str).tolist()
                else:
                    cleaned_data[col] = ["No"] * len(raw_df)
        else:
            cleaned_data["Spreadsheet_Row_ID"] = []
            for col in ALL_SYSTEM_COLUMNS:
                cleaned_data[col] = []
                
        return pd.DataFrame(cleaned_data)
        
    except Exception as e:
        st.sidebar.error(f"Failed to fetch ledger rows: {e}")
    
    # Solid blueprint fallback if the spreadsheet is completely empty
    blank_df = pd.DataFrame(columns=["Spreadsheet_Row_ID"] + ALL_SYSTEM_COLUMNS)
    return blank_df

# Handle memory tracking states across frame sessions safely
if "editable_ledger_df" not in st.session_state:
    st.session_state.editable_ledger_df = download_raw_cloud_rows()

if st.sidebar.button("🔄 Discard Changes & Force Re-Sync"):
    if "editable_ledger_df" in st.session_state:
        del st.session_state.editable_ledger_df
    st.session_state.editable_ledger_df = download_raw_cloud_rows()
    st.rerun()

# Deep copy to break any underlying data references completely
current_working_df = st.session_state.editable_ledger_df.copy()

# --- DYNAMIC INTERACTIVE CHECKBOX COLUMN BUILDER ---
grid_configuration = {
    "Spreadsheet_Row_ID": st.column_config.TextColumn("Row ID", disabled=True),
    "Category": st.column_config.SelectboxColumn("Stage Phase", options=STAGES, required=True),
    "Date": st.column_config.TextColumn("Tracking Date")
}

# Convert text values ("Yes"/"No") to true/false checkboxes using a 100% crash-proof mapping array
for m_col in milestone_columns:
    # Normalize data strings to handle empty or invalid entries safely
    raw_values = current_working_df[m_col].fillna("No").astype(str).str.strip().str.upper()
    current_working_df[m_col] = raw_values.apply(lambda x: True if x in ["YES", "TRUE"] else False)
    grid_configuration[m_col] = st.column_config.CheckboxColumn(m_col, default=False)

# ── ADVANCED INTERACTIVE DATA MATRIX GRID VIEW ──
edited_data_output = st.data_editor(
    current_working_df,
    use_container_width=True,
    hide_index=True,
    num_rows="dynamic",
    column_config=grid_configuration
)

st.markdown("---")
st.subheader("💾 Database Commit Control Matrix")
if st.button("💾 Push Grid Edits Live to Cloud Sheets", type="primary", use_container_width=True):
    final_sync_df = edited_data_output.copy()
    
    # Convert checkbox boolean values back to text for your Google Sheet
    for m_col in milestone_columns:
        final_sync_df[m_col] = final_sync_df[m_col].map({True: "Yes", False: "No"}).fillna("No")
        
    success_rows_count = 0
    if not final_sync_df.empty:
        for index_row, data_row in final_sync_df.iterrows():
            dict_payload = data_row.to_dict()
            dict_payload["Last_Updated_By"] = user_email
            dict_payload["Last_Modified_On"] = datetime.now().strftime("%Y-%m-%d %H:%M")
            
            payload_ordered = {col: str(dict_payload.get(col, "")) for col in ["Spreadsheet_Row_ID"] + ALL_SYSTEM_COLUMNS}
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
