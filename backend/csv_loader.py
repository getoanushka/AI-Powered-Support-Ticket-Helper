import pandas as pd
from typing import Dict, List
from pathlib import Path

ROOT = Path(__file__).parent

class CSVLoader:
    def __init__(self, data_dir: str = None):
        # Default to repository-relative backend/data directory
        if data_dir:
            self.data_dir = Path(data_dir)
        else:
            self.data_dir = ROOT / 'data'
    
    def load_tickets(self, filename: str = 'tickets.csv') -> pd.DataFrame:
        """
        Load tickets from CSV file.
        """
        filepath = Path(self.data_dir) / filename
        df = pd.read_csv(filepath)
        return df
    
    def load_kb_articles(self, filename: str = 'kb_articles.csv') -> pd.DataFrame:
        """
        Load KB articles from CSV file.
        """
        filepath = Path(self.data_dir) / filename
        df = pd.read_csv(filepath)
        return df
    
    def get_tickets_as_dict(self) -> List[Dict]:
        """
        Get tickets as list of dictionaries.
        """
        df = self.load_tickets()
        return df.to_dict('records')
    
    def get_kb_articles_as_dict(self) -> List[Dict]:
        """
        Get KB articles as list of dictionaries.
        """
        df = self.load_kb_articles()
        return df.to_dict('records')