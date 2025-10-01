"""
Automated scheduler for Substack analytics data collection.
Runs periodic scraping and analysis tasks.
"""

import schedule
import time
import logging
from datetime import datetime
from enhanced_collector import SubstackDataCollector
from analytics import SubstackAnalytics
import os

class SubstackScheduler:
    """Automated scheduler for Substack analytics."""
    
    def __init__(self, db_path="substack_analytics.db"):
        self.db_path = db_path
        self.analytics = SubstackAnalytics(db_path)
        
        # Set up logging
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler('scheduler.log'),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger(__name__)
    
    def scrape_publication(self, publication_name, max_posts=50):
        """Scrape a specific publication."""
        try:
            self.logger.info(f"Starting scheduled scrape for {publication_name}")
            
            collector = SubstackDataCollector(publication_name, self.db_path)
            publication_data = collector.scrape_publication_info()
            posts = collector.scrape_posts(max_posts)
            collector.save_to_database(posts, publication_data)
            
            self.logger.info(f"Successfully scraped {len(posts)} posts for {publication_name}")
            return True
            
        except Exception as e:
            self.logger.error(f"Error scraping {publication_name}: {e}")
            return False
    
    def daily_scrape(self, publications):
        """Daily scraping task."""
        self.logger.info("Starting daily scraping task")
        
        for pub in publications:
            self.scrape_publication(pub, max_posts=20)  # Limit for daily updates
            time.sleep(30)  # Rate limiting between publications
        
        self.logger.info("Daily scraping task completed")
    
    def weekly_analysis(self, publications):
        """Weekly analysis task."""
        self.logger.info("Starting weekly analysis task")
        
        for pub in publications:
            try:
                # Generate comprehensive analytics
                engagement = self.analytics.get_engagement_metrics(pub, days_back=7)
                growth = self.analytics.get_growth_metrics(pub, days_back=30)
                insights = self.analytics.get_content_insights(pub, days_back=7)
                
                # Log key metrics
                self.logger.info(f"Weekly metrics for {pub}:")
                self.logger.info(f"  - Posts: {engagement.get('total_posts', 0)}")
                self.logger.info(f"  - Words: {engagement.get('total_words', 0):,}")
                self.logger.info(f"  - Growth: {growth.get('posts_growth_rate', 0)}%")
                
                # Export weekly report
                export_data = self.analytics.get_export_data(pub)
                filename = f"weekly_report_{pub}_{datetime.now().strftime('%Y%m%d')}.json"
                
                import json
                with open(filename, 'w') as f:
                    json.dump(export_data, f, indent=2, default=str)
                
                self.logger.info(f"Weekly report saved: {filename}")
                
            except Exception as e:
                self.logger.error(f"Error in weekly analysis for {pub}: {e}")
        
        self.logger.info("Weekly analysis task completed")
    
    def cleanup_old_data(self, days_to_keep=90):
        """Clean up old data to keep database size manageable."""
        try:
            import sqlite3
            from datetime import datetime, timedelta
            
            cutoff_date = datetime.now() - timedelta(days=days_to_keep)
            
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Delete old posts
            cursor.execute("DELETE FROM posts WHERE published_at < ?", (cutoff_date,))
            deleted_posts = cursor.rowcount
            
            # Delete old analytics
            cursor.execute("DELETE FROM analytics WHERE created_at < ?", (cutoff_date,))
            deleted_analytics = cursor.rowcount
            
            conn.commit()
            conn.close()
            
            self.logger.info(f"Cleanup completed: {deleted_posts} posts, {deleted_analytics} analytics records removed")
            
        except Exception as e:
            self.logger.error(f"Error during cleanup: {e}")
    
    def start_scheduler(self, publications, daily_scrape=True, weekly_analysis=True, cleanup=True):
        """Start the automated scheduler."""
        self.logger.info("Starting Substack Analytics Scheduler")
        self.logger.info(f"Tracking publications: {', '.join(publications)}")
        
        # Schedule daily scraping (6 AM)
        if daily_scrape:
            schedule.every().day.at("06:00").do(self.daily_scrape, publications)
            self.logger.info("Daily scraping scheduled for 6:00 AM")
        
        # Schedule weekly analysis (Sunday 8 AM)
        if weekly_analysis:
            schedule.every().sunday.at("08:00").do(self.weekly_analysis, publications)
            self.logger.info("Weekly analysis scheduled for Sunday 8:00 AM")
        
        # Schedule monthly cleanup (1st of month at 2 AM)
        if cleanup:
            schedule.every().month.do(self.cleanup_old_data)
            self.logger.info("Monthly cleanup scheduled")
        
        self.logger.info("Scheduler started. Press Ctrl+C to stop.")
        
        try:
            while True:
                schedule.run_pending()
                time.sleep(60)  # Check every minute
        except KeyboardInterrupt:
            self.logger.info("Scheduler stopped by user")
        except Exception as e:
            self.logger.error(f"Scheduler error: {e}")

def main():
    """Main function to run the scheduler."""
    # List of publications to track
    publications = [
        "platformer",  # Example publication
        # Add more publications here
    ]
    
    # Initialize scheduler
    scheduler = SubstackScheduler()
    
    # Start the scheduler
    scheduler.start_scheduler(
        publications=publications,
        daily_scrape=True,
        weekly_analysis=True,
        cleanup=True
    )

if __name__ == "__main__":
    main()
