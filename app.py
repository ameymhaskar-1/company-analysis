import streamlit as st
import pandas as pd
import datetime
from io import BytesIO
import traceback

from src.company_resolver import CompanyResolver
from src.data_pipeline.orchestrator import DataOrchestrator
from src.excel_generator import generate_excel_workbook

# --- 1. APP CONFIGURATION ---
st.set_page_config(page_title="Indian Equity Analyzer", layout="wide", page_icon="📈")

# --- 2. INITIALIZE SESSION STATE ---
if 'processed_data' not in st.session_state:
    st.session_state['processed_data'] = None
if 'resolver' not in st.session_state:
    st.session_state['resolver'] = CompanyResolver()
    
resolver = st.session_state['resolver']

# --- 3. UI LAYOUT & INPUTS ---
st.title("📈 Indian Equity Fundamental Analyzer")
st.markdown("Analyze Indian listed companies using real market data, SEC/NSE filings, and RSS feeds.")
st.divider()

col1, col2, col3 = st.columns(3)

with col1:
    st.subheader("Company Selection")
    search_query = st.text_input("Search Company Name, NSE Symbol, or ISIN:")
    available_companies = resolver.get_all_companies()
    
    # Auto-resolve from search query
    filtered_companies = available_companies
    if search_query:
        filtered_companies = resolver.search(search_query)
        st.caption(f"Found {len(filtered_companies)} matches.")
        
    selected_companies = st.multiselect(
        "Select Companies (N dynamic)", 
        options=filtered_companies['SYMBOL'].tolist() if not filtered_companies.empty else [],
        help="Select any number of companies. No limits."
    )
    
    pasted_tickers = st.text_input("Or paste comma-separated NSE Tickers:")
    if pasted_tickers:
        additional = [t.strip().upper() for t in pasted_tickers.split(",") if t.strip()]
        selected_companies = list(set(selected_companies + additional))

with col2:
    st.subheader("Historical Period")
    current_year = datetime.datetime.now().year
    opt_5yr = f"5 Years (Up to {current_year})"
    opt_10yr = f"10 Years (Up to {current_year})"
    history_choice = st.selectbox("Select history depth:", [opt_5yr, opt_10yr])
    years_to_fetch = 5 if "5" in history_choice else 10

with col3:
    st.subheader("Statement Type")
    statement_type = st.radio("Select format:", ["Consolidated", "Standalone"])

st.divider()
fetch_button = st.button("🚀 FETCH & ANALYZE (Real Data)", type="primary", use_container_width=True)

# --- 4. DATA PIPELINE EXECUTION ---
if fetch_button:
    if not selected_companies:
        st.error("Please select at least one company.")
        st.stop()
        
    st.subheader("Processing Status")
    progress_bar = st.progress(0)
    
    orchestrator = DataOrchestrator(years_to_fetch, statement_type)
    
    success_count = 0
    failed_companies = []
    total_companies = len(selected_companies)
    
    # Master Data Containers
    master_data = {
        'financials': [], 'market_data': [], 'metrics': [], 'shareholding': [], 
        'dividends': [], 'risk_flags': [], 'annual_reports': [], 'data_quality': []
    }
    
    # Fault-Tolerant Loop with Granular UI Status
    for i, symbol in enumerate(selected_companies):
        
        # Create an expanding status box for EACH company
        with st.status(f"Processing {i+1}/{total_companies}: {symbol}...", expanded=True) as status_box:
            
            def update_ui(msg):
                # This callback updates the text inside the status box in real-time
                status_box.update(label=msg)
                
            try:
                company_meta = resolver.get_company_info(symbol)
                
                # Process company using the orchestrator (with timeouts managed inside)
                company_data = orchestrator.process_company(company_meta, status_callback=update_ui)
                
                # Append successfully retrieved real data
                for key in master_data:
                    if key in company_data and not company_data[key].empty:
                        master_data[key].append(company_data[key])
                
                success_count += 1
                status_box.update(label=f"✓ {symbol} Complete!", state="complete", expanded=False)
                
            except Exception as e:
                err_msg = str(e)
                failed_companies.append((symbol, err_msg))
                # Log the exact error to the UI without stopping the batch
                status_box.update(label=f"✗ {symbol} Failed: {err_msg}", state="error", expanded=True)
                
        # Update overall batch progress bar
        progress_bar.progress((i + 1) / total_companies)
        
    # Concat all real data lists into Master DataFrames
    st.session_state['processed_data'] = {
        k: pd.concat(v, ignore_index=True) if v else pd.DataFrame() 
        for k, v in master_data.items()
    }
    st.session_state['selected_companies'] = selected_companies

    # Final summary banner
    st.success(f"Batch Complete! Successfully processed: {success_count} | Failed: {len(failed_companies)} | Total: {total_companies}")
    
# --- 5. DASHBOARD & EXCEL EXPORT ---
if st.session_state.get('processed_data') and not st.session_state['processed_data']['market_data'].empty:
    st.divider()
    st.header("Executive Dashboard")
    st.dataframe(st.session_state['processed_data']['market_data'].set_index('Company'))
    
    st.subheader("📥 Download Analysis")
    with st.spinner("Generating 26-sheet Excel workbook..."):
        excel_buffer = BytesIO()
        generate_excel_workbook(excel_buffer, st.session_state['processed_data'], st.session_state['selected_companies'])
        excel_buffer.seek(0)
        
        st.download_button(
            label="DOWNLOAD COMPLETE EXCEL ANALYSIS",
            data=excel_buffer,
            file_name=f"Real_Equity_Analysis_{datetime.datetime.now().strftime('%Y%m%d')}.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            type="primary"
        )
