import os
import requests
from typing import Dict

class SlackAlerts:
    def __init__(self, webhook_url: str = None):
        self.webhook_url = webhook_url or os.getenv('SLACK_WEBHOOK_URL')

    def send_message(self, text: str) -> bool:
        if not self.webhook_url:
            raise RuntimeError('SLACK_WEBHOOK_URL not configured')
        payload = {"text": text}
        resp = requests.post(self.webhook_url, json=payload, timeout=10)
        return resp.status_code == 200

    def send_gap_alert(self, gap_data: Dict) -> bool:
        # Format a compact Slack-friendly message
        summary = gap_data.get('summary', {})
        msg = f"*KB Article Performance Alert*\n"
        msg += f"Total Articles: {summary.get('total_articles',0)}\n"
        msg += f"Average CTR: {summary.get('avg_ctr',0):.2%}\n"
        msg += f"Low Performers: {summary.get('low_performers_count',0)}\n"
        msg += f"Low Coverage: {summary.get('low_coverage_count',0)}\n"

        # Add top low performers
        if gap_data.get('low_performers'):
            msg += "\n*Top low performers:*\n"
            for art in gap_data['low_performers'][:5]:
                msg += f"• {art.get('title','<no title>')} (CTR: {art.get('ctr',0):.2%})\n"

        try:
            return self.send_message(msg)
        except Exception:
            return False
