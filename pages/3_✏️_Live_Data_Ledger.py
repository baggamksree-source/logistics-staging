import streamlit as st
import pandas as pd
import requests
import json
import time
import io
from utils import COLUMNS, STAGES

st.set_page_config(page_title="Ledger Interface", layout="wide")

st.title("✏️ Master Interactive Shipments Data Ledger")
st.caption("Read pipeline: Hybrid Fail-Safe Sync Activated (Auto-Mapping Model).")

PRODUCTION_WRITE_URL = st.secrets["sheet_write_url"]
RAW_READ_URL = st.secrets["sheet_read_url"]

milestone_columns = [
    "SO", "Empty container pickup", "Laden containers gatein", "SOB", 
    "Draft BL Checking and Approval", "Pre-alert documents", "Remittance", 
    "Telex/original bl", "FC", "Odex filing/manual", "Invoice", "DO", 
    "Empty containers return"
]

def fetch_master_dataframe_direct():
    # Pipeline Corridor: Direct Read Engine (Attempts fast download first)
    try:
        clean_url = RAW_READ_URL
        if "/edit" in clean_url:
            clean_url = clean_url.split('/edit')[0] + "/export?format=csv&gid=0"
        elif "/export" not in clean_url:
            clean_url = clean_url.rstrip('/') + "/export?format=csv&gid=0"
            
        sync_link = f"{clean_url}&ts={int(time.time() * 1000)}"
        response = requests.get(sync_link, timeout=5)
        
        if response.status_code == 200 and response.text.strip():
            raw_text_lines = response.text.strip().split('\n')
            if len(raw_text_lines) > 2:
                data_body_csv = "\n".join(raw_text_lines[2:])
                df = pd.read_csv(io.StringIO(data_body_csv), header=None).fillna("")
                return process_extracted_dataframe(df)
    except:
        pass

    # Backup Pipeline Corridor: AppsScript Stream Read Engine
    try:
        st.sidebar.warning("⚡ Primary channel locked. Deploying AppsScript fallback...")
        fallback_link = f"{PRODUCTION_WRITE_URL}?ts={int(time.time() * 1000)}"
        response = requests.get(fallback_link, timeout=15)
        
        if response.status_code == 200 and response.text.strip():
            raw_text_lines = response.text.strip().split('\n')
            if len(raw_text_lines) > 1:
                data_body_csv = "\n".join(raw_text_lines[1:])
                df = pd.read_csv(io.StringIO(data_body_csv), header=None).fillna("")
                return process_extracted_dataframe(df)
    except Exception as e:
        st.sidebar.error(f"All database connection channels exhausted: {e}")
        
    return pd.DataFrame()

def process_extracted_dataframe(raw_df):
    columns_pool = list(COLUMNS)
    current_data_cols_count = len(raw_df.columns)
    
    # Dynamic header count map adapter
    if current_data_cols_count < len(columns_pool):
        columns_pool = columns_pool[:current_data_cols_count]
    elif current_data_cols_count > len(columns_pool):
        for diff in range(current_data_cols_count - len(columns_pool)):
            columns_pool.append(f"Field_{diff+1}")
            
    raw_df.columns = columns_pool
    df_processed = raw_df.copy()
    
    # Calculate physical sheet row positions accurately
    df_processed["Spreadsheet_Row_ID"] = [str(i + 3) for i in range(len(df_processed))]
    
    # Safely find the routing stage column without failing
    category_col = None
    for col in df_processed.columns:
        if str(col).lower().strip() == "category":
            category_col = col
            break
            
    if category_col:
        df_processed["Category_Cleaned"] = df_processed[category_col].astype(str).str.strip()
        df_processed["Stage_Priority"] = df_processed["Category_Cleaned"].map({
            "Yet to sail": 1, "On water": 2, "Reached shore yet to release": 3,
            "Released": 4, "Empty container returned": 5
        }).fillna(6)
        df_processed = df_processed.sort_values(by=["Stage_Priority", "Spreadsheet_Row_ID"], ascending=[True, True])
        df_processed = df_processed.drop(columns=["Category_Cleaned", "Stage_Priority"], errors="ignore")
        
    final_cols_order = ["Spreadsheet_Row_ID"] + [c for c in df_processed.columns if c != "Spreadsheet_Row_ID"]
    return df_processed[final_cols_order]

# Dynamic Session Cache Core
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
    
    # Automatically scan columns and assign checkbox selectors to milestones
    for col in working_df.columns:
        if col in milestone_columns:
            grid_configuration[col] = st.column_config.CheckboxColumn(col, default=False)
        elif str(col).lower().strip() == "category":
            grid_configuration[col] = st.column_config.SelectboxColumn(col, options=STAGES, required=True)
            
    st.markdown("🟢 **Master Consolidated Queue Line**")
    edited_output = st.data_editor(working_df, use_container_width=True, hide_index=True, column_config=grid_configuration, key="data_ledger_grid_master_unified")
        
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
                requests.post(PRODUCTION_WRITE_URL, data=json.dumps(payload_ordered), headers={"Content-Type": "application/json"})
                success_rows_count += 1
            except:
                pass
        st.success(f"✓ Success! Grid variations synchronized live. ({success_rows_count} items matched).")
        time.sleep(1)
        st.session_state.pop('ledger_fresh_data', None)
        st.rerun()
else:
    st.warning("⚠️ Formatting grid structure mapping... Please click the 'Force Re-Sync' button in the sidebar.")
