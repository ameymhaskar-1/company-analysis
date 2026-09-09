import yfinance as yf
import pandas as pd
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

class TimeoutSession(requests.Session):
    """Custom requests session that enforces strict timeouts globally."""
    def request(self, *args, **kwargs):
        kwargs.setdefault('timeout', (5, 15)) # 5s connect, 15s read
        return super().request(*args, **kwargs)

class YFinanceProvider:
    def __init__(self, ticker_str):
        self.ticker_str = ticker_str
        self.source_name = "Yahoo Finance API"
        
        # Build robust session
        self.session = TimeoutSession()
        retry = Retry(total=3, backoff_factor=1, status_forcelist=[429, 500, 502, 503, 504])
        adapter = HTTPAdapter(max_retries=retry)
        self.session.mount('http://', adapter)
        self.session.mount('https://', adapter)
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'
        })
        
        # Inject the timeout session into yfinance
        self.ticker = yf.Ticker(ticker_str, session=self.session)
        
    def fetch_market_data(self):
        try:
            info = self.ticker.info
            return {
                'Market Cap': info.get('marketCap', pd.NA),
                'Current Price': info.get('currentPrice', pd.NA),
                '52W High': info.get('fiftyTwoWeekHigh', pd.NA),
                '52W Low': info.get('fiftyTwoWeekLow', pd.NA),
                'P/E': info.get('trailingPE', pd.NA),
                'P/B': info.get('priceToBook', pd.NA),
                'Dividend Yield': info.get('dividendYield', pd.NA),
                'Beta': info.get('beta', pd.NA),
            }
        except Exception as e:
            print(f"[{self.ticker_str}] YFinance Market Data Error: {e}")
            return {}

    def fetch_financials(self, max_years):
        try:
            inc_stmt = self.ticker.financials
            bs = self.ticker.balance_sheet
            cf = self.ticker.cashflow
            
            data = []
            def _get_val(df, metric, dt):
                try: return df.loc[metric, dt]
                except KeyError: return pd.NA

            available_dates = list(inc_stmt.columns)[:max_years] if not inc_stmt.empty else []
            for dt in available_dates:
                fy = f"FY{dt.year}"
                metrics = {
                    'Revenue': ('Total Revenue', inc_stmt),
                    'EBITDA': ('EBITDA', inc_stmt),
                    'PAT': ('Net Income', inc_stmt),
                    'Total Assets': ('Total Assets', bs),
                    'Total Liabilities Net Minority Interest': ('Total Liabilities Net Minority Interest', bs),
                    'Operating Cash Flow': ('Operating Cash Flow', cf),
                    'Capital Expenditure': ('Capital Expenditure', cf)
                }
                
                for m_name, (m_key, df_src) in metrics.items():
                    val = _get_val(df_src, m_key, dt)
                    if pd.notna(val):
                        data.append({
                            'Financial Year': fy, 'Period End': dt.strftime('%Y-%m-%d'),
                            'Metric': m_name, 'Value': val, 'Unit': 'INR',
                            'Source': self.source_name, 'Reported/Calculated': 'Reported'
                        })
            return pd.DataFrame(data)
        except Exception as e:
            print(f"[{self.ticker_str}] YFinance Financials Error: {e}")
            return pd.DataFrame()
