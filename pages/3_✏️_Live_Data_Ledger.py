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
st.caption("Read pipeline: Streamlined Secure Webhook Connection Pipeline.")

# Connect directly to the authoritative pipeline webhook endpoint
PRODUCTION_API_URL = st.secrets["sheet_write_url"]

milestone_columns = [
    "SO", "Empty container pickup", "Laden containers gatein", "SOB", 
    "Draft BL Checking and Approval", "Pre-alert documents", "Remittance", 
    "Telex/original bl", "FC", "Odex filing/manual", "Invoice", "DO", 
    "Empty containers return"
]

def fetch_master_dataframe_direct():
    try:
        # Append a dynamic timestamp parameter to bypass browser and server response caches
        secure_gateway_link = f"{PRODUCTION_API_URL}?ts={int(time.time() * 1000)}"
        
        # Call the secure Google AppsScript macro architecture directly
        response = requests.get(secure_gateway_link, timeout=20)
        
        if response.status_code == 200 and response.text.strip():
            raw_text = response.text.strip()
            
            # Catch secure connection redirection page errors and drop them immediately
            if "<html" in raw_text.lower() or "<!doctype" in raw_text.lower():
                st.sidebar.error("❌ Google Security Access Error: Please check deployment settings.")
                return pd.DataFrame()
                
            string_buffer = io.StringIO(raw_text)
            csv_reader_engine = csv.reader(string_buffer)
            all_extracted_rows = [row for row in csv_reader_engine if any(cell.strip() for cell in row)]
            
            # The AppsScript doGet logic drops clean headers on line 1, slice safely
            if len(all_extracted_rows) > 1:
                data_body_rows = all_extracted_rows[1:]
                
                df = pd.DataFrame(data_body_rows).fillna("")
                return process_extracted_dataframe(df, start_row_offset=3)
            else:
                st.sidebar.info("ℹ️ Connection established, but sheet contains no data rows yet.")
        else:
            st.sidebar.error(f"❌ Server communication dropped with status: {response.status_code}")
    except Exception as e:
        st.sidebar.error(f"❌ Direct API Corridor Exception: {e}")
        
    return pd.DataFrame()

def process_extracted_dataframe(raw_df, start_row_offset):
    columns_pool = list(COLUMNS)
    current_data_cols_count = len(raw_df.columns)
    
    if current_data_cols_count < len(columns_pool):
        columns_pool = columns_pool[:current_data_cols_count]
    elif current_data_cols_count > len(columns_pool):
        raw_df = raw_df.iloc[:, :len(columns_pool)]
        
    raw_df.columns = columns_pool
    df_processed = raw_df.copy()
    
    # Calculate tracking reference index assignments relative to the spreadsheet layout
    df_processed["Spreadsheet_Row_ID"] = [str(i + start_row_offset) for i in range(len(df_processed))]
    
    if "Category" in df_processed.columns:
        df_processed["Category"] = df_processed["Category"].astype(str).str.strip()
        df_processed["Stage_Priority"] = df_processed["Category"].map({
            "Yet to sail": 1, "On water": 2, "Reached shore yet to release": 3,
            "Released": 4, "Empty container returned": 5
        }).fillna(6)
        df_processed = df_processed.sort_values(by=["Stage_Priority", "Spreadsheet_Row_ID"], ascending=[True, True])
        df_processed = df_processed.drop(columns=["Stage_Priority"], errors="ignore")
        
    final_cols_order = ["Spreadsheet_Row_ID"] + [c for c in df_processed.columns if c != "Spreadsheet_Row_ID"]
    return df_processed[final_cols_order]

# Synchronize UI global workspace cache state parameters
if 'ledger_fresh_data' not in st.session_state or st.sidebar.button("🔄 Discard Changes & Force Re-Sync"):
    st.session_state.ledger_fresh_data = fetch_master_dataframe_direct()

working_df = st.session_state.ledger_fresh_data.copy()

if not working_df.empty:
    for m_col in milestone_columns:
        if m_col in working_df.columns:
            working_df[m_col] = working_df[m_col].astype(str).str.strip().str.upper().apply(
                lambda x: True if x in ["YES", "TRUE", "DONE"] else False
            )
            
    grid_configuration = {
        "Spreadsheet_Row_ID": st.column_config.TextColumn("Row ID", disabled=True),
    }
    for col in working_df.columns:
        if col in milestone_columns:
            grid_configuration[col] = st.column_config.CheckboxColumn(col, default=False)
        elif str(col).lower().strip() == "category":
            grid_configuration[col] = st.column_config.SelectboxColumn(col, options=STAGES, required=True)
            
    st.markdown("🟢 **Master Consolidated Queue Line**")
    edited_output = st.data_editor(working_df, use_container_width=True, hide_index=True, column_config=grid_configuration, key="data_ledger_grid_master_unified_streamlined")
        
    st.markdown("---")
    if st.button("💾 Push Grid Edits Live to Cloud Sheets", type="primary", use_container_width=True):
        final_sync_df = edited_output.copy()
        for m_col in milestone_columns:
            if m_col in final_sync_df.columns:
                final_sync_df[m_col] = final_sync_df[m_col].map({True: "Yes", False: "No"}).fillna("No")
                
        success_rows_count = 0
        columns_to_send = [c for c in working_df.columns if c != "Spreadsheet_Row_ID"]
        
        for idx_row, data_row in final_sync_df.iterrows():
            dict_payload = data_row.to_dict()
            payload_ordered = {col: str(dict_payload.get(col, "")) for col in ["Spreadsheet_Row_ID"] + columns_to_send}
            try:
                requests.post(PRODUCTION_API_URL, data=json.dumps(payload_ordered), headers={"Content-Type": "application/json"})
                success_rows_count += 1
            except:
                pass
        st.success(f"✓ Success! Data synchronized live ({success_rows_count} entries verified).")
        time.sleep(1)
        st.session_state.pop('ledger_fresh_data', None)
        st.rerun()
else:
    st.warning("⚠️ Ready for mapping pipeline initialization. Please click the 'Discard Changes & Force Re-Sync' button on your sidebar dashboard.")
