import pandas as pd
import requests
import io
import streamlit as st

class CompanyResolver:
    def __init__(self):
        self.master_df = self._fetch_nse_master()

    @st.cache_data(ttl=86400)
    def _fetch_nse_master(_self):
        """Fetches the actual NSE listed companies CSV to avoid hardcoding limits."""
        url = "https://nsearchives.nseindia.com/content/equities/EQUITY_L.csv"
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'}
        try:
            response = requests.get(url, headers=headers, timeout=10)
            if response.status_code == 200:
                df = pd.read_csv(io.StringIO(response.text))
                return df[['SYMBOL', 'NAME OF COMPANY', ' ISIN NUMBER']]
        except Exception:
            pass # Fallback if NSE blocks direct request
        
        # Fallback dictionary if NSE API block is active
        return pd.DataFrame([
            {'SYMBOL': 'TCS', 'NAME OF COMPANY': 'Tata Consultancy Services Limited', ' ISIN NUMBER': 'INE467B01029'},
            {'SYMBOL': 'RELIANCE', 'NAME OF COMPANY': 'Reliance Industries Limited', ' ISIN NUMBER': 'INE002A01018'},
            {'SYMBOL': 'HDFCBANK', 'NAME OF COMPANY': 'HDFC Bank Limited', ' ISIN NUMBER': 'INE040A01034'},
            {'SYMBOL': 'INFY', 'NAME OF COMPANY': 'Infosys Limited', ' ISIN NUMBER': 'INE009A01021'}
        ])

    def get_all_companies(self):
        return self.master_df

    def search(self, query):
        q = str(query).upper()
        return self.master_df[
            self.master_df['SYMBOL'].str.contains(q, na=False) |
            self.master_df['NAME OF COMPANY'].str.upper().str.contains(q, na=False)
        ]

    def get_company_info(self, symbol):
        match = self.master_df[self.master_df['SYMBOL'] == symbol]
        if not match.empty:
            return {
                'symbol': symbol,
                'name': match.iloc[0]['NAME OF COMPANY'],
                'isin': match.iloc[0][' ISIN NUMBER'],
                'yfinance_ticker': f"{symbol}.NS"
            }
        return {'symbol': symbol, 'name': symbol, 'yfinance_ticker': f"{symbol}.NS"}
