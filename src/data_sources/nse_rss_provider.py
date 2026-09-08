import feedparser
import pandas as pd
from datetime import datetime

class NSERssProvider:
    def __init__(self, symbol):
        self.symbol = symbol
        
    def fetch_corporate_actions(self):
        """Fetches real NSE Corporate actions from XML RSS Feeds"""
        # Note: Actual NSE RSS requires valid session. This parses the feed if accessible.
        url = f"https://www.nseindia.com/rss/company/{self.symbol}.xml"
        feed = feedparser.parse(url)
        
        actions = []
        for entry in feed.entries:
            actions.append({
                'Date': entry.get('published', datetime.now().strftime("%Y-%m-%d")),
                'Title': entry.get('title', 'N/A'),
                'Link': entry.get('link', 'N/A'),
                'Source': 'NSE Official RSS'
            })
            
        df = pd.DataFrame(actions)
        if not df.empty:
            df['Company'] = self.symbol
        return df
