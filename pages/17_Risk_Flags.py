import streamlit as st
import pandas as pd

st.set_page_config(page_title="Risk Flags", layout="wide")
st.title("Automated Risk Analysis")

data = st.session_state.get('processed_data')

if data is None or 'financials' not in data or data['financials'].empty:
    st.error("Data required.")
else:
    df = data['financials']
    risk_logs = []
    
    # Actual Rule: Detect negative PAT
    pat_df = df[df['Metric'] == 'PAT']
    for _, row in pat_df.iterrows():
        if pd.notna(row['Value']) and row['Value'] < 0:
            risk_logs.append({
                'Company': row['Company'], 'Year': row['Financial Year'],
                'Risk Flag': 'Negative Net Income', 'Severity': 'High',
                'Observed Value': row['Value']
            })
            
    if risk_logs:
        st.error("Risks Detected:")
        st.dataframe(pd.DataFrame(risk_logs))
    else:
        st.success("No High Severity Risks Detected in current dataset.")
