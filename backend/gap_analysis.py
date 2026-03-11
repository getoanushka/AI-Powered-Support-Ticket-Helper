import pandas as pd
from typing import Dict, List
import numpy as np

from pathlib import Path

class GapAnalyzer:
    def __init__(self, kb_articles_csv: str = None):
        if kb_articles_csv is None:
            kb_articles_csv = Path(__file__).resolve().parent / 'data' / 'kb_articles.csv'
        self.kb_articles_csv = str(kb_articles_csv)
    
    def load_articles_with_analytics(self) -> pd.DataFrame:
        """
        Load KB articles with view and click data.
        """
        df = pd.read_csv(self.kb_articles_csv)
        return df
    
    def calculate_ctr(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Calculate Click-Through Rate (CTR) for each article.
        """
        df['ctr'] = df['clicks'] / df['views']
        df['ctr'] = df['ctr'].fillna(0)
        return df
    
    def identify_low_performers(self, df: pd.DataFrame, 
                               ctr_threshold: float = 0.2) -> pd.DataFrame:
        """
        Identify articles with low CTR.
        """
        low_performers = df[df['ctr'] < ctr_threshold].copy()
        low_performers = low_performers.sort_values('ctr')
        return low_performers
    
    def identify_low_coverage(self, df: pd.DataFrame, 
                            views_threshold: int = 300) -> pd.DataFrame:
        """
        Identify articles with low view counts (potential coverage gaps).
        """
        low_coverage = df[df['views'] < views_threshold].copy()
        low_coverage = low_coverage.sort_values('views')
        return low_coverage
    
    def analyze_gaps(self) -> Dict:
        """
        Perform full gap analysis.
        """
        # Load articles
        df = self.load_articles_with_analytics()
        
        # Calculate CTR
        df = self.calculate_ctr(df)
        
        # Identify issues
        low_performers = self.identify_low_performers(df)
        low_coverage = self.identify_low_coverage(df)
        
        # Calculate statistics
        avg_ctr = df['ctr'].mean()
        avg_views = df['views'].mean()
        avg_clicks = df['clicks'].mean()
        
        return {
            'summary': {
                'total_articles': len(df),
                'avg_ctr': float(avg_ctr),
                'avg_views': float(avg_views),
                'avg_clicks': float(avg_clicks),
                'low_performers_count': len(low_performers),
                'low_coverage_count': len(low_coverage)
            },
            'low_performers': low_performers.to_dict('records'),
            'low_coverage': low_coverage.to_dict('records'),
            'all_articles': df.to_dict('records')
        }