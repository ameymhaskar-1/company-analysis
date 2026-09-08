import streamlit as st
import pandas as pd
import plotly.express as px

st.set_page_config(page_title="Financial Statements", layout="wide")
st.title("Financial Statements")

data = st.session_state.get('processed_data')

if data is None or 'financials' not in data or data['financials'].empty:
    st.error("No financial data found. Please run FETCH & ANALYZE on the main page.")
else:
    df = data['financials']
    st.dataframe(df)
    
    # Render actual chart based on data
    if 'Metric' in df.columns and 'Value' in df.columns:
        metrics = df['Metric'].unique()
        selected_metric = st.selectbox("Select Metric to Visualize:", metrics)
        
        filtered = df[df['Metric'] == selected_metric]
        if not filtered.empty:
            fig = px.bar(filtered, x='Financial Year', y='Value', color='Company', title=f'{selected_metric} Trend')
            st.plotly_chart(fig, use_container_width=True)
