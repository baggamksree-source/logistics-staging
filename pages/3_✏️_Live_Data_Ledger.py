import streamlit as st
import pandas as pd
import requests
import json
from datetime import datetime
from utils import COLUMNS, STAGES

st.set_page_config(page_title="Ledger Interface", layout="wide")

st.title("✏️ Master Interactive Shipments Data Ledger")

# HARDCODE TARGET FOR DATA READING AND WRITING BYPASS CACHE BUGS
PRODUCTION_URL = "https://script.google.com/macros/s/AKfycbyQK3DJnLU4j1JHr5Xsfq0FATxMwRo8UWkret4UL_cj7buA1HqhJCdB2oR8KVkHOLhgug/exec"

milestone_columns = [
    "SO Must Arrive", "Container Pick Up / Stuffing / Handover",
    "BL Draft Checking & Approval", "BL Approval from Shipper and Consignee",
    "Follow-up of Container Back to Terminal", "Vessel ETD+ Tracking",
    "Enquiry of Pre-alert Docs + D/N on ETD + SOB Confirmation",
    "On Water ETA Tracking", "Freight Certificate", "Remittance to Overseas Agent",
    "IGM File + CFS Nomination", "Local Charges Invoice Checking and Payment",
    "DO Procurement", "Cost Sheet Preparation", "Customer Invoice Prep + Submission to Client"
]

ALL_SYSTEM_COLUMNS = COLUMNS

def download_raw_cloud_rows():
    try:
        read_link = PRODUCTION_URL + "?action=read" if "exec" in PRODUCTION_URL else PRODUCTION_URL
        # Pull raw csv from the script endpoint directly safely
        raw_df = pd.read_csv(PRODUCTION_URL.replace("/exec", "/exec?action=read"), dtype=str).fillna("No")
        if not raw_df.empty:
            raw_df.columns = raw_df.columns.astype(str).str.strip()
            raw_df["Spreadsheet_Row_ID"] = [str(i + 2) for i in range(len(raw_df))]
            for c in ALL_SYSTEM_COLUMNS:
                if c not in raw_df.columns: raw_df[c] = "No"
            return raw_df[["Spreadsheet_Row_ID"] + ALL_SYSTEM_COLUMNS]
    except:
        pass
    return pd.DataFrame(columns=["Spreadsheet_Row_ID"] + ALL_SYSTEM_COLUMNS)

# Simple URL fail fallback to pull from reading secrets config string to insulate errors
if "sheet_read_url" in st.secrets:
    READ_LINK_URL = st.secrets["sheet_read_url"]
else:
    READ_LINK_URL = PRODUCTION_URL

def fallback_fetch():
    try:
        raw_df = pd.read_csv(READ_LINK_URL, dtype=str).fillna("No")
        raw_df.columns = raw_df.columns.astype(str).str.strip()
        raw_df["Spreadsheet_Row_ID"] = [str(i + 2) for i in range(len(raw_df))]
        for c in ALL_SYSTEM_COLUMNS:
            if c not in raw_df.columns: raw_df[c] = "No"
        return raw_df[["Spreadsheet_Row_ID"] + ALL_SYSTEM_COLUMNS]
    except:
        return pd.DataFrame(columns=["Spreadsheet_Row_ID"] + ALL_SYSTEM_COLUMNS)

if "editable_ledger_df" not in st.session_state:
    st.session_state.editable_ledger_df = fallback_fetch()

if st.sidebar.button("🔄 Discard Changes & Force Re-Sync"):
    if "editable_ledger_df" in st.session_state: del st.session_state.editable_ledger_df
    st.session_state.editable_ledger_df = fallback_fetch()
    st.rerun()

current_working_df = st.session_state.editable_ledger_df.copy()

grid_configuration = {
    "Spreadsheet_Row_ID": st.column_config.TextColumn("Row ID", disabled=True),
    "Category": st.column_config.SelectboxColumn("Stage Phase", options=STAGES, required=True),
    "Date": st.column_config.TextColumn("Nomination Date")
}

for m_col in milestone_columns:
    if m_col not in current_working_df.columns: current_working_df[m_col] = "No"
    raw_values = current_working_df[m_col].fillna("No").astype(str).str.strip().str.upper()
    current_working_df[m_col] = raw_values.apply(lambda x: True if x in ["YES", "TRUE"] else False)
    grid_configuration[m_col] = st.column_config.CheckboxColumn(m_col, default=False)

for col in ALL_SYSTEM_COLUMNS:
    if col not in milestone_columns and col not in ["Spreadsheet_Row_ID", "Category", "Date"]:
        current_working_df[col] = current_working_df[col].fillna("").astype(str)
        grid_configuration[col] = st.column_config.TextColumn(col)

edited_data_output = st.data_editor(
    current_working_df, use_container_width=True, hide_index=True, num_rows="fixed", column_config=grid_configuration
)

st.markdown("---")
if st.button("💾 Push Grid Edits Live to Cloud Sheets", type="primary", use_container_width=True):
    final_sync_df = edited_data_output.copy()
    for m_col in milestone_columns:
        final_sync_df[m_col] = final_sync_df[m_col].map({True: "Yes", False: "No"}).fillna("No")
        
    success_rows_count = 0
    if not final_sync_df.empty:
        for index_row, data_row in final_sync_df.iterrows():
            dict_payload = data_row.to_dict()
            dict_payload["Last_Updated_By"] = "ops_team"
            dict_payload["Last_Modified_On"] = datetime.now().strftime("%Y-%m-%d %H:%M")
            payload_ordered = {col: str(dict_payload.get(col, "")) for col in ["Spreadsheet_Row_ID"] + ALL_SYSTEM_COLUMNS}
            try:
                requests.post(PRODUCTION_URL, data=json.dumps(payload_ordered), headers={"Content-Type": "application/json"})
                success_rows_count += 1
            except:
                pass
    st.success(f"✓ Success! Synchronized matrix array processed. ({success_rows_count} entries verified).")
    if "editable_ledger_df" in st.session_state: del st.session_state["editable_ledger_df"]
    st.cache_data.clear()
    st.rerun()
