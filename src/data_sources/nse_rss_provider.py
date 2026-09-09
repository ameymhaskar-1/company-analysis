import feedparser
import pandas as pd
import requests
from datetime import datetime
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

class NSERssProvider:
    def __init__(self, symbol):
        self.symbol = symbol
        self.source_name = "NSE Official RSS"
        
        # Robust Session with Retries and strict Timeouts
        self.session = requests.Session()
        retry = Retry(total=2, backoff_factor=1, status_forcelist=[403, 429, 500, 502, 503, 504])
        self.session.mount('https://', HTTPAdapter(max_retries=retry))
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'application/rss+xml'
        })

    def fetch_corporate_actions(self):
        url = f"https://www.nseindia.com/rss/company/{self.symbol}.xml"
        actions = []
        try:
            # STRICT TIMEOUT: 5s connection, 10s read. Prevents infinite hanging.
            resp = self.session.get(url, timeout=(5, 10))
            resp.raise_for_status()
            
            # Pass the securely downloaded string to feedparser
            feed = feedparser.parse(resp.content)
            
            for entry in feed.entries:
                actions.append({
                    'Date': entry.get('published', datetime.now().strftime("%Y-%m-%d")),
                    'Title': entry.get('title', 'N/A'),
                    'Link': entry.get('link', 'N/A'),
                    'Source': self.source_name
                })
        except requests.exceptions.Timeout:
            print(f"[{self.symbol}] ⚠ NSE RSS Timeout after 15s")
        except Exception as e:
            print(f"[{self.symbol}] ⚠ NSE RSS Error: {e}")
            
        df = pd.DataFrame(actions)
        if not df.empty:
            df['Company'] = self.symbol
        return df
