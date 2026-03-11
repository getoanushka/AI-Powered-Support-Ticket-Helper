import json
from datetime import datetime
from typing import Dict
import os
from pathlib import Path

from pathlib import Path

class AlertLogger:
    def __init__(self, log_dir: str = None):
        if log_dir is None:
            log_dir = Path(__file__).resolve().parent / 'logs'
        self.log_dir = str(log_dir)
        os.makedirs(self.log_dir, exist_ok=True)
    
    def log_gap_analysis(self, gap_data: Dict):
        """
        Log gap analysis results.
        """
        timestamp = datetime.now().strftime('%Y-%m-%d_%H-%M-%S')
        log_file = os.path.join(self.log_dir, f'gap_analysis_{timestamp}.json')
        
        with open(log_file, 'w') as f:
            json.dump(gap_data, f, indent=2)
        
        print(f"Gap analysis logged to {log_file}")
    
    def format_alert_message(self, gap_data: Dict) -> str:
        """
        Format gap analysis data into human-readable alert message.
        """
        summary = gap_data['summary']
        
        message = f"""📊 KB Article Performance Alert
━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

📈 Summary:
  • Total Articles: {summary['total_articles']}
  • Average CTR: {summary['avg_ctr']:.2%}
  • Average Views: {summary['avg_views']:.0f}
  • Average Clicks: {summary['avg_clicks']:.0f}

⚠️ Issues Detected:
  • Low Performers: {summary['low_performers_count']} articles
  • Low Coverage: {summary['low_coverage_count']} articles
"""
        
        if gap_data['low_performers']:
            message += "\n🔻 Top 3 Low Performing Articles:\n"
            for i, article in enumerate(gap_data['low_performers'][:3], 1):
                message += f"  {i}. {article['title']} (CTR: {article['ctr']:.2%})\n"
        
        if gap_data['low_coverage']:
            message += "\n📉 Top 3 Low Coverage Articles:\n"
            for i, article in enumerate(gap_data['low_coverage'][:3], 1):
                message += f"  {i}. {article['title']} (Views: {article['views']})\n"
        
        return message
    
    def send_alert(self, gap_data: Dict):
        """
        Send alert (currently logs to file and prints).
        In production, this would send to Slack webhook.
        """
        # Log to file
        self.log_gap_analysis(gap_data)
        
        # Format and print alert
        message = self.format_alert_message(gap_data)
        print("\n" + "="*50)
        print(message)
        print("="*50 + "\n")
        
        # Save alert message to latest log
        alert_file = os.path.join(self.log_dir, 'latest_alert.txt')
        with open(alert_file, 'w') as f:
            f.write(message)