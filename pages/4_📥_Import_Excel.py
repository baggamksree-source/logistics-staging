import streamlit as st
import pandas as pd
import requests
import json
from utils import COLUMNS, STAGES

st.set_page_config(page_title="Excel Importer", layout="wide")

if not st.session_state.get("security_cleared", False):
    st.error("🔒 Security Authentication Required. Go to Home Hub page first."); st.stop()

st.title("📥 Logistics Excel Batch Import Engine")
st.caption("Upload `.xlsx` or `.xls` spreadsheets. Missing data inputs or milestones default to empty values so you can fill them manually later inside the Live Ledger.")

PRODUCTION_URL = "PASTE_YOUR_OFFICE_ID_WEB_APP_URL_HERE"

# 🏭 Structural Data Template Guide Layout for users
st.info("💡 **Formatting Rule:** For best results, name your Excel sheet columns similarly to your master spreadsheet headers (e.g., 'Customer', 'Booking_MBL', 'HBL', 'Container'). Any mismatched headers can be left empty!")

uploaded_file = st.file_uploader("📂 Select Cargo Excel Manifest File to Process", type=["xlsx", "xls"])

if uploaded_file is not None:
    try:
        # Read uploaded sheets into memory safely
        excel_data_df = pd.read_excel(uploaded_file, dtype=str).fillna("")
        
        st.subheader("👀 Raw Upload Data Preview")
        st.dataframe(excel_data_df.head(10), use_container_width=True)
        
        st.markdown("---")
        st.subheader("🛠️ Database Dynamic Alignment Verification")
        
        # Build dynamic drop selectors to match user excel columns to our 31 master headers
        mapping_dictionary = {}
        columns_layout_grid = st.columns(3)
        
        # Guide mapping for key operational identifiers
        critical_match_keys = ["Date", "Category", "Customer", "Agent", "HBL", "Liner", "Booking_MBL", "Container", "POL", "POD"]
        
        st.markdown("##### 🔗 Realign Crucial Shipment Tracking Parameters")
        for idx, master_col in enumerate(COLUMNS):
            # Try to guess matching columns automatically to save user manual selection clicks
            default_index_selection = 0
            lowercase_excel_cols = [str(c).lower().strip() for c in excel_data_df.columns]
            target_match_clean = master_col.lower().replace("_", " ").strip()
            
            if master_col.lower() in lowercase_excel_cols:
                default_index_selection = lowercase_excel_cols.index(master_col.lower()) + 1
            elif target_match_clean in lowercase_excel_cols:
                default_index_selection = lowercase_excel_cols.index(target_match_clean) + 1
                
            grid_slot = idx % 3
            with columns_layout_grid[grid_slot]:
                selected_excel_header = st.selectbox(
                    f"Match Sheet Column for: **{master_col}**",
                    options=["-- Leave Cell Empty / Default No --"] + list(excel_data_df.columns),
                    index=default_index_selection,
                    key=f"map_drop_{master_col}"
                )
                if selected_excel_header != "-- Leave Cell Empty / Default No --":
                    mapping_dictionary[master_col] = selected_excel_header

        st.markdown("---")
        
        # Execution button layout
        if st.button("🚀 Push Entire Excel Batch Live to Cloud Google Sheet", type="primary", use_container_width=True):
            records_processing_bar = st.progress(0)
            successful_injections_counter = 0
            total_records_to_process = len(excel_data_df)
            
            for index_row, excel_row in excel_data_df.iterrows():
                # Construct standard 31 column production blueprint dictionary mapping
                processed_row_payload = {}
                for master_col in COLUMNS:
                    if master_col in mapping_dictionary:
                        processed_row_payload[master_col] = str(excel_row[mapping_dictionary[master_col]]).strip()
                    else:
                        # Fallback default settings: Milestones default to "No", stages default to "Yet to sail"
                        if "Must Arrive" in master_col or "/" in master_col or "Tracking" in master_col or "Certificate" in master_col or "Payment" in master_col or "Procurement" in master_col or "Preparation" in master_col or "Prep" in master_col:
                            processed_row_payload[master_col] = "No"
                        elif master_col == "Category":
                            processed_row_payload[master_col] = "Yet to sail"
                        else:
                            processed_row_payload[master_col] = ""
                            
                # Push direct webhook transaction package
                try:
                    response = requests.post(PRODUCTION_URL, data=json.dumps(processed_row_payload), headers={"Content-Type": "application/json"})
                    if response.status_code == 200:
                        successful_injections_counter += 1
                except:
                    pass
                
                # Advance tracking bar state display
                current_percent_done = int(((index_row + 1) / total_records_to_process) * 100)
                records_processing_bar.progress(current_percent_done)
                
            st.success(f"🎉 BATCH IMPORT COMPLETE! Successfully injected {successful_injections_counter} rows straight into your Master Sheet1 database tab!")
            st.cache_data.clear()
            
    except Exception as general_error:
        st.error(f"❌ Spreadsheet Parsing Error: {general_error}. Make sure your file formatting has clean column definitions.")
