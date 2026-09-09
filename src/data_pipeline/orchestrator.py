import pandas as pd
import datetime
from src.data_sources.yfinance_provider import YFinanceProvider
from src.data_sources.nse_rss_provider import NSERssProvider

class DataOrchestrator:
    def __init__(self, years, stmt_type):
        self.years = years
        self.stmt_type = stmt_type

    def process_company(self, company_meta):
        symbol = company_meta['symbol']
        yf_ticker = company_meta['yfinance_ticker']
        
        yf_prov = YFinanceProvider(yf_ticker)
        nse_prov = NSERssProvider(symbol)
        
        # 1. Market Data
        mkt_dict = yf_prov.fetch_market_data()
        mkt_dict['Company'] = symbol
        mkt_df = pd.DataFrame([mkt_dict])
        
        # 2. Financials Data
        fin_df = yf_prov.fetch_financials(self.years)
        if not fin_df.empty:
            fin_df['Company'] = symbol
            fin_df['Statement Type'] = self.stmt_type
            
        # 3. Shareholding / RSS actions
        rss_df = nse_prov.fetch_corporate_actions()
        
        # 4. Data Quality Audit
        dq_df = pd.DataFrame([{
            'Company': symbol,
            'Status': 'Success' if not fin_df.empty else 'Partial/Failed',
            'Financials Found': len(fin_df) > 0,
            'Market Data Found': pd.notna(mkt_dict.get('Current Price', pd.NA)),
            'Timestamp': datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }])
        
        # Calculate real metrics like ROE (Net Income / Assets approx) if data exists
        metrics_df = pd.DataFrame()
        if not fin_df.empty:
            try:
                # Pivot for calculation
                calc_pvt = fin_df.pivot_table(index='Financial Year', columns='Metric', values='Value').reset_index()
                if 'PAT' in calc_pvt.columns and 'Total Assets' in calc_pvt.columns:
                    calc_pvt['ROA'] = (calc_pvt['PAT'] / calc_pvt['Total Assets']) * 100
                    
                # Melt back into normalized structure
                metrics_data = []
                for _, row in calc_pvt.iterrows():
                    if 'ROA' in row and pd.notna(row['ROA']):
                        metrics_data.append({
                            'Company': symbol, 'Financial Year': row['Financial Year'],
                            'Metric': 'ROA', 'Value': row['ROA'], 'Unit': '%',
                            'Reported/Calculated': 'Calculated', 'Source': 'System'
                        })
                metrics_df = pd.DataFrame(metrics_data)
            except Exception:
                pass
                
        return {
            'market_data': mkt_df,
            'financials': fin_df,
            'metrics': metrics_df,
            'corporate_actions': rss_df,
            'data_quality': dq_df
        }
