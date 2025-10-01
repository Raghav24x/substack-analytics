"""
Example script demonstrating how to use the Substack Analytics tools.
"""

from enhanced_collector import SubstackDataCollector
from analytics import SubstackAnalytics
import json

def main():
    print("Substack Analytics Example")
    print("=" * 50)
    
    # Example publication name (you can change this)
    publication_name = "platformer"  # This will scrape platformer.substack.com
    
    print(f"Analyzing publication: {publication_name}")
    print()
    
    # Step 1: Initialize the data collector
    print("1. Initializing data collector...")
    collector = SubstackDataCollector(publication_name)
    
    # Step 2: Scrape publication information
    print("2. Scraping publication information...")
    publication_data = collector.scrape_publication_info()
    print(f"   Found publication: {publication_data.name}")
    print(f"   Author: {publication_data.author}")
    print(f"   Description: {publication_data.description[:100]}...")
    print()
    
    # Step 3: Scrape posts
    print("3. Scraping posts (this may take a few minutes)...")
    posts = collector.scrape_posts(max_posts=20)  # Limit to 20 posts for demo
    print(f"   Scraped {len(posts)} posts")
    print()
    
    # Step 4: Save to database
    print("4. Saving data to database...")
    collector.save_to_database(posts, publication_data)
    print("   Data saved successfully")
    print()
    
    # Step 5: Initialize analytics
    print("5. Running analytics...")
    analytics = SubstackAnalytics()
    
    # Get engagement metrics
    engagement = analytics.get_engagement_metrics(publication_name, days_back=30)
    print("   Engagement Metrics:")
    print(f"      - Total Posts: {engagement.get('total_posts', 0)}")
    print(f"      - Total Words: {engagement.get('total_words', 0):,}")
    print(f"      - Average Word Count: {engagement.get('avg_word_count', 0)}")
    print(f"      - Average Read Time: {engagement.get('avg_read_time', 0)} minutes")
    print(f"      - Premium Posts: {engagement.get('premium_posts', 0)}")
    print()
    
    # Get growth metrics
    growth = analytics.get_growth_metrics(publication_name, days_back=30)
    print("   Growth Metrics:")
    print(f"      - Posts Growth Rate: {growth.get('posts_growth_rate', 0)}%")
    print(f"      - Words Growth Rate: {growth.get('words_growth_rate', 0)}%")
    print(f"      - Average Posts per Day: {growth.get('avg_posts_per_day', 0)}")
    print()
    
    # Get content insights
    insights = analytics.get_content_insights(publication_name, days_back=30)
    print("   Content Insights:")
    print(f"      - Average Title Length: {insights.get('title_analysis', {}).get('avg_length', 0)}")
    print(f"      - Top Words: {[word for word, count in insights.get('common_words', [])[:5]]}")
    print()
    
    # Show recommendations
    recommendations = insights.get('recommendations', [])
    if recommendations:
        print("   Recommendations:")
        for i, rec in enumerate(recommendations, 1):
            print(f"      {i}. {rec}")
        print()
    
    # Step 6: Export data
    print("6. Exporting data...")
    export_data = analytics.get_export_data(publication_name)
    
    # Save to JSON file
    filename = f"{publication_name}_analytics_export.json"
    with open(filename, 'w') as f:
        json.dump(export_data, f, indent=2, default=str)
    print(f"   Data exported to {filename}")
    
    # Export CSV
    collector.export_to_csv(f"{publication_name}_analytics")
    print(f"   CSV files exported")
    print()
    
    print("Analysis complete!")
    print(f"Check the generated files:")
    print(f"   - {filename}")
    print(f"   - {publication_name}_analytics_posts.csv")
    print(f"   - {publication_name}_analytics_publication.csv")
    print()
    print("To view the web dashboard, run: python main.py")
    print("   Then open: http://localhost:5000")

if __name__ == "__main__":
    main()
