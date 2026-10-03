import streamlit as st
import pandas as pd
import requests
import json
import time
import io
from utils import COLUMNS, STAGES

st.set_page_config(page_title="Ledger Interface", layout="wide")

st.title("✏️ Master Interactive Shipments Data Ledger")
st.caption("Read pipeline: Auto-healing column index data mapping enabled.")

PRODUCTION_WRITE_URL = st.secrets["sheet_write_url"]
RAW_READ_URL = st.secrets["sheet_read_url"]

milestone_columns = [
    "SO", "Empty container pickup", "Laden containers gatein", "SOB", 
    "Draft BL Checking and Approval", "Pre-alert documents", "Remittance", 
    "Telex/original bl", "FC", "Odex filing/manual", "Invoice", "DO", 
    "Empty containers return"
]

def fetch_master_dataframe_direct():
    try:
        # Split share link and convert to a direct export download pipeline
        base_url = RAW_READ_URL.split('/edit')
        csv_download_pipe = f"{base_url[0]}/export?format=csv&gid=0&ts={int(time.time() * 1000)}"
        
        response = requests.get(csv_download_pipe, timeout=15)
        
        if response.status_code != 200 or not response.text.strip():
            st.sidebar.error("Could not retrieve a valid data stream from the cloud storage engine.")
            return pd.DataFrame()
            
        # Read the raw sheet data line-by-line to properly parse the double-wrapped header row layout
        raw_text_lines = response.text.strip().split('\n')
        if len(raw_text_lines) <= 2:
            return pd.DataFrame()
            
        # DYNAMIC MATCHING ENGINE: Safely extract rows 3 onwards, skipping the broken headers entirely
        data_body_csv = "\n".join(raw_text_lines[2:])
        raw_df = pd.read_csv(io.StringIO(data_body_csv), header=None).fillna("")
        
        # Clip columns array length definitions dynamically to match structural counts
        columns_pool = list(COLUMNS)
        current_data_cols_count = len(raw_df.columns)
        
        if current_data_cols_count < len(columns_pool):
            columns_pool = columns_pool[:current_data_cols_count]
        elif current_data_cols_count > len(columns_pool):
            # Pad array boundaries if the sheet contains extra legacy rows
            for diff in range(current_data_cols_count - len(columns_pool)):
                columns_pool.append(f"Legacy_Field_{diff+1}")
                
        raw_df.columns = columns_pool
        
        # Clean up key index matching structures to align maps cleanly
        if "Category" not in raw_df.columns:
            st.error("Header Alignment Warning: Could not locate 'Category' phase tracking column.")
            return pd.DataFrame()
            
        # Reconstruct actual physical spreadsheet row IDs matching index maps
        raw_df["Spreadsheet_Row_ID"] = [str(i + 3) for i in range(len(raw_df))]
        
        # Strip invisible text spaces from data parameters
        raw_df["Category"] = raw_df["Category"].astype(str).str.strip()
        
        raw_df["Stage_Priority"] = raw_df["Category"].map({
            "Yet to sail": 1, "On water": 2, "Reached shore yet to release": 3,
            "Released": 4, "Empty container returned": 5
        }).fillna(6)
        
        raw_df = raw_df.sort_values(by=["Stage_Priority", "Spreadsheet_Row_ID"], ascending=[True, True])
        
        final_cols_order = ["Spreadsheet_Row_ID"] + [c for c in columns_pool if c != "Spreadsheet_Row_ID"]
        return raw_df[final_cols_order]
    except Exception as e:
        st.sidebar.error(f"Extraction Pipeline Interruption: {e}")
        return pd.DataFrame()

# Inject fresh dataset rows values instantly
if 'ledger_fresh_data' not in st.session_state or st.sidebar.button("🔄 Discard Changes & Force Re-Sync"):
    st.session_state.ledger_fresh_data = fetch_master_dataframe_direct()
    if not st.session_state.ledger_fresh_data.empty:
        st.toast("Database tables updated live!", icon="⚡")

working_df = st.session_state.ledger_fresh_data.copy()

def apply_phase_color_rows(row):
    phase = str(row.get("Category", "")).strip()
    if phase == "Yet to sail": return ["background-color: #FFFFFF; color: #000000"] * len(row)
    elif phase == "On water": return ["background-color: #E2F0D9; color: #385723"] * len(row)
    elif phase == "Reached shore yet to release": return ["background-color: #DDEBF7; color: #1F4E78"] * len(row)
    elif phase == "Released": return ["background-color: #F2F2F2; color: #595959"] * len(row)
    elif phase == "Empty container returned": return ["background-color: #E1F5FE; color: #01579B"] * len(row)
    return [""] * len(row)

if not working_df.empty:
    # Process milestone string flags into valid Streamlit interactive checkmark values
    for m_col in milestone_columns:
        if m_col in working_df.columns:
            working_df[m_col] = working_df[m_col].astype(str).str.strip().str.upper().apply(
                lambda x: True if x in ["YES", "TRUE", "DONE"] else False
            )
            
    grid_configuration = {
        "Spreadsheet_Row_ID": st.column_config.TextColumn("Row ID", disabled=True),
        "Category": st.column_config.SelectboxColumn("Stage Phase", options=STAGES, required=True),
    }
    for m_col in milestone_columns:
        if m_col in working_df.columns:
            grid_configuration[m_col] = st.column_config.CheckboxColumn(m_col, default=False)
            
    def render_interactive_grid(df_dataset, dynamic_key_suffix):
        styled_df = df_dataset.style.apply(apply_phase_color_rows, axis=1)
        return st.data_editor(styled_df, use_container_width=True, hide_index=True, column_config=grid_configuration, key=f"data_ledger_grid_{dynamic_key_suffix}")
        
    tab_master, tab_yts, tab_ow, tab_rs = st.tabs(["📊 All Sorted Shipments Grid View", "⛵ Yet to Sail Only", "🌊 On Water Active", "⚓ Reached Shore / Released"])
    
    with tab_master:
        st.markdown("🟢 **Master Consolidated Queue Line**")
        edited_output = render_interactive_grid(working_df, "master_view")
        
    with tab_yts:
        st.markdown("⛵ **Isolated View: Unshipped Freight Bookings**")
        render_interactive_grid(working_df[working_df["Category"] == "Yet to sail"], "yet_to_sail_view")
        
    with tab_ow:
        st.markdown("🌊 **Isolated View: Active High Sea Transits**")
        render_interactive_grid(working_df[working_df["Category"] == "On water"], "on_water_view")
        
    with tab_rs:
        st.markdown("⚓ **Isolated View: Arrived / Cargo Delivered Records**")
        render_interactive_grid(working_df[working_df["Category"].isin(["Reached shore yet to release", "Released", "Empty container returned"])], "shore_released_view")
        
    st.markdown("---")
    if st.button("💾 Push Grid Edits Live to Cloud Sheets", type="primary", use_container_width=True):
        final_sync_df = edited_output.copy()
        for m_col in milestone_columns:
            if m_col in final_sync_df.columns:
                final_sync_df[m_col] = final_sync_df[m_col].map({True: "Yes", False: "No"}).fillna("No")
                
        success_rows_count = 0
        columns_to_send = [c for c in working_df.columns if c != "Stage_Priority"]
        
        for idx_row, data_row in final_sync_df.iterrows():
            dict_payload = data_row.to_dict()
            payload_ordered = {col: str(dict_payload.get(col, "")) for col in columns_to_send}
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
    st.warning("⚠️ Access pipe open. Checking master row layout matrix bounds...")
