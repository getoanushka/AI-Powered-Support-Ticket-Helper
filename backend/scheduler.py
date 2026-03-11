from apscheduler.schedulers.background import BackgroundScheduler
from gap_analysis import GapAnalyzer
from alert_logger import AlertLogger
from slack_alerts import SlackAlerts
import logging
import os

logger = logging.getLogger(__name__)


def run_daily_analysis():
    """
    Run daily gap analysis and send alerts.
    If `SLACK_WEBHOOK_URL` is set, post to Slack; otherwise fallback to file logger.
    """
    try:
        logger.info("Running daily gap analysis...")

        # Analyze gaps
        analyzer = GapAnalyzer()
        gap_data = analyzer.analyze_gaps()

        # Send alerts via Slack if configured
        slack_url = os.getenv('SLACK_WEBHOOK_URL')
        if slack_url:
            slack = SlackAlerts(slack_url)
            sent = slack.send_gap_alert(gap_data)
            if sent:
                logger.info('Slack alert sent successfully')
            else:
                logger.warning('Slack alert failed; falling back to file logger')
                AlertLogger().send_alert(gap_data)
        else:
            # No Slack configured — log locally
            AlertLogger().send_alert(gap_data)

        logger.info("Daily gap analysis completed")
    except Exception as e:
        logger.error(f"Error in daily analysis: {str(e)}")


def start_scheduler():
    """
    Start the background scheduler.
    Runs gap analysis every 24 hours.
    """
    scheduler = BackgroundScheduler()

    # Schedule daily analysis (runs every 24 hours)
    scheduler.add_job(run_daily_analysis, 'interval', hours=24)

    # Also run once on startup
    scheduler.add_job(run_daily_analysis, 'date')

    scheduler.start()
    logger.info("Scheduler started - daily gap analysis enabled")

    return scheduler


if __name__ == '__main__':
    # For testing
    logging.basicConfig(level=logging.INFO)
    run_daily_analysis()