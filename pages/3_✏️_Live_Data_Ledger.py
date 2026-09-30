import streamlit as st
import pandas as pd
import requests
import json
import time
import io
import csv
from utils import COLUMNS, STAGES

st.set_page_config(page_title="Ledger Interface", layout="wide")

st.title("✏️ Master Interactive Shipments Data Ledger")
st.caption("Records are fully sorted: 'Yet to sail' sits locked on top, followed immediately by 'On water' items.")

# Routing directly through your working Apps Script Web App Endpoint
PRODUCTION_URL = st.secrets["sheet_write_url"]

milestone_columns = [
    "SO Must Arrive", "Container Pick Up / Stuffing / Handover",
    "BL Draft Checking & Approval", "BL Approval from Shipper and Consignee",
    "Follow-up of Container Back to Terminal", "Vessel ETD+ Tracking",
    "Enquiry of Pre-alert Docs + D/N on ETD + SOB Confirmation",
    "On Water ETA Tracking", "Freight Certificate", "Remittance to Overseas Agent",
    "IGM File + CFS Nomination", "Local Charges Invoice Checking and Payment",
    "DO Procurement", "Cost Sheet Preparation", "Customer Invoice Prep + Submission to Client"
]

def fetch_master_dataframe():
    try:
        # Calls the doGet(e) method inside your healthy script pipeline
        sync_link = f"{PRODUCTION_URL}?ts={int(time.time())}"
        response = requests.get(sync_link, timeout=15)
        
        if response.status_code != 200 or not response.text.strip():
            st.sidebar.warning("⚠️ Connected safely, but sheet cell data is currently empty.")
            return pd.DataFrame(columns=["Spreadsheet_Row_ID"] + COLUMNS)
            
        # Parse text stream safely through memory buffers
        raw_text_stream = io.StringIO(response.text.strip())
        csv_reader_engine = csv.reader(raw_text_stream)
        all_parsed_rows = list(csv_reader_engine)
        
        if len(all_parsed_rows) <= 1:
            return pd.DataFrame(columns=["Spreadsheet_Row_ID"] + COLUMNS)
            
        extracted_headers = [str(h).strip() for h in all_parsed_rows[0]]
        data_body_rows = all_parsed_rows[1:]
        
        df = pd.DataFrame(data_body_rows, columns=extracted_headers).fillna("")
        df.columns = df.columns.astype(str).str.strip()
        
        df["Spreadsheet_Row_ID"] = [str(i + 2) for i in range(len(df))]
        
        for col in COLUMNS:
            if col not in df.columns: 
                df[col] = ""
                
        # --- ENFORCED PRIORITY SORTING PIPELINE LOGIC ---
        df["Stage_Priority"] = df["Category"].map({
            "Yet to sail": 1, "On water": 2, "Reached shore yet to release": 3,
            "Released": 4, "Empty container returned": 5
        }).fillna(6)
        
        df = df.sort_values(by=["Stage_Priority", "Spreadsheet_Row_ID"], ascending=[True, True])
        return df[["Spreadsheet_Row_ID"] + COLUMNS]
    except Exception as e:
        st.sidebar.error(f"Sync Issue: {e}")
        return pd.DataFrame(columns=["Spreadsheet_Row_ID"] + COLUMNS)

if "editable_ledger_df" not in st.session_state:
    st.session_state.editable_ledger_df = fetch_master_dataframe()

if st.sidebar.button("🔄 Discard Changes & Force Re-Sync"):
    if "editable_ledger_df" in st.session_state: 
        del st.session_state.editable_ledger_df
    st.session_state.editable_ledger_df = fetch_master_dataframe()
    st.rerun()

def apply_phase_color_rows(row):
    phase = str(row["Category"]).strip()
    if phase == "Yet to sail": return ["background-color: #FFFFFF; color: #000000"] * len(row)
    elif phase == "On water": return ["background-color: #E2F0D9; color: #385723"] * len(row)
    elif phase == "Reached shore yet to release": return ["background-color: #DDEBF7; color: #1F4E78"] * len(row)
    elif phase == "Released": return ["background-color: #F2F2F2; color: #595959"] * len(row)
    elif phase == "Empty container returned": return ["background-color: #E1F5FE; color: #01579B"] * len(row)
    return [""] * len(row)

tab_master, tab_yts, tab_ow, tab_rs = st.tabs(["📊 All Sorted Shipments Grid View", "⛵ Yet to Sail Only", "🌊 On Water Active", "⚓ Reached Shore / Released"])

raw_working_data = st.session_state.editable_ledger_df.copy()

for m_col in milestone_columns:
    if m_col in raw_working_data.columns:
        raw_working_data[m_col] = raw_working_data[m_col].astype(str).str.strip().str.upper().apply(lambda x: True if x in ["YES", "TRUE"] else False)

grid_configuration = {
    "Spreadsheet_Row_ID": st.column_config.TextColumn("Row ID", disabled=True),
    "Category": st.column_config.SelectboxColumn("Stage Phase", options=STAGES, required=True),
}
for m_col in milestone_columns:
    grid_configuration[m_col] = st.column_config.CheckboxColumn(m_col, default=False)

def render_interactive_grid(df_dataset, dynamic_key_suffix):
    styled_df = df_dataset.style.apply(apply_phase_color_rows, axis=1)
    return st.data_editor(styled_df, use_container_width=True, hide_index=True, num_rows="fixed", column_config=grid_configuration, key=f"data_ledger_grid_{dynamic_key_suffix}")

with tab_master:
    st.markdown("🟢 **Master Consolidated Queue Line**")
    edited_output = render_interactive_grid(raw_working_data, "master_view")

with tab_yts:
    st.markdown("⛵ **Isolated View: Unshipped Freight Bookings**")
    render_interactive_grid(raw_working_data[raw_working_data["Category"] == "Yet to sail"], "yet_to_sail_view")

with tab_ow:
    st.markdown("🌊 **Isolated View: Active High Sea Transits**")
    render_interactive_grid(raw_working_data[raw_working_data["Category"] == "On water"], "on_water_view")

with tab_rs:
    st.markdown("⚓ **Isolated View: Arrived / Cargo Delivered Records**")
    render_interactive_grid(raw_working_data[raw_working_data["Category"].isin(["Reached shore yet to release", "Released", "Empty container returned"])], "shore_released_view")

st.markdown("---")
if st.button("💾 Push Grid Edits Live to Cloud Sheets", type="primary", use_container_width=True):
    final_sync_df = edited_output.copy()
    for m_col in milestone_columns:
        final_sync_df[m_col] = final_sync_df[m_col].map({True: "Yes", False: "No"}).fillna("No")
        
    success_rows_count = 0
    if not final_sync_df.empty:
        for idx_row, data_row in final_sync_df.iterrows():
            dict_payload = data_row.to_dict()
            payload_ordered = {col: str(dict_payload.get(col, "")) for col in ["Spreadsheet_Row_ID"] + COLUMNS}
            try:
                requests.post(PRODUCTION_URL, data=json.dumps(payload_ordered), headers={"Content-Type": "application/json"})
                success_rows_count += 1
            except:
                pass
    st.success(f"✓ Success! Synchronized matrix array processed. ({success_rows_count} entries verified).")
    if "editable_ledger_df" in st.session_state: 
        del st.session_state["editable_ledger_df"]
    st.rerun()
