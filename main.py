"""
Main application for Substack Analytics Dashboard.
Run this to start the complete analytics system.
"""

import os
import sys
from flask import Flask, render_template, jsonify, request, send_file
import sqlite3
import pandas as pd
import json
from datetime import datetime
from enhanced_collector import SubstackDataCollector
from analytics import SubstackAnalytics

app = Flask(__name__)

class SubstackAnalyticsApp:
    """Main application class for Substack Analytics."""
    
    def __init__(self, db_path="substack_analytics.db"):
        self.db_path = db_path
        self.collectors = {}
        self.analytics = SubstackAnalytics(db_path)
    
    def add_publication(self, publication_name):
        """Add a new publication to track."""
        collector = SubstackDataCollector(publication_name, self.db_path)
        self.collectors[publication_name] = collector
        return collector

    def get_collector(self, publication_name):
        """Get an existing collector or create one if data exists."""
        collector = self.collectors.get(publication_name)
        if collector:
            return collector

        publication_data = self.get_publication_data(publication_name)
        if not publication_data:
            return None

        collector = SubstackDataCollector(publication_name, self.db_path)
        self.collectors[publication_name] = collector
        return collector
    
    def get_publications(self):
        """Get list of tracked publications."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT DISTINCT name FROM publication")
        publications = [row[0] for row in cursor.fetchall()]
        conn.close()
        return publications
    
    def get_publication_data(self, publication_name):
        """Get publication data."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM publication WHERE name = ?", (publication_name,))
        row = cursor.fetchone()
        conn.close()
        
        if row:
            return {
                'name': row[1],
                'description': row[2],
                'url': row[3],
                'subscriber_count': row[4],
                'posts_count': row[5],
                'author': row[7],
                'social_links': json.loads(row[8]) if row[8] else {}
            }
        return None
    
    def scrape_publication(self, publication_name, max_posts=100):
        """Scrape data for a publication."""
        collector = self.add_publication(publication_name)
        publication_data = collector.scrape_publication_info()
        posts = collector.scrape_posts(max_posts)
        collector.save_to_database(posts, publication_data)
        
        return {
            'status': 'success',
            'posts_count': len(posts),
            'publication': publication_data
        }

# Initialize app
analytics_app = SubstackAnalyticsApp()

@app.route('/')
def index():
    """Main dashboard page."""
    publications = analytics_app.get_publications()
    return render_template('index.html', publications=publications)

@app.route('/api/publications')
def api_publications():
    """Get all publications."""
    publications = analytics_app.get_publications()
    return jsonify(publications)

@app.route('/api/publication/<publication_name>')
def api_publication(publication_name):
    """Get publication data."""
    data = analytics_app.get_publication_data(publication_name)
    if data:
        return jsonify(data)
    return jsonify({'error': 'Publication not found'}), 404

@app.route('/api/posts/<publication_name>')
def api_posts(publication_name):
    """Get posts data."""
    conn = sqlite3.connect(analytics_app.db_path)
    limit = request.args.get('limit', 50, type=int)
    
    query = '''
        SELECT * FROM posts 
        WHERE url LIKE ? 
        ORDER BY published_at DESC 
        LIMIT ?
    '''
    posts_df = pd.read_sql_query(query, conn, params=(f"%{publication_name}%", limit))
    conn.close()
    
    posts_data = []
    for _, post in posts_df.iterrows():
        posts_data.append({
            'title': post['title'],
            'url': post['url'],
            'excerpt': post['excerpt'],
            'author': post['author'],
            'published_at': post['published_at'],
            'word_count': post['word_count'],
            'read_time': post['read_time'],
            'likes': int(post['likes']) if not pd.isna(post['likes']) else 0,
            'comments': int(post['comments']) if not pd.isna(post['comments']) else 0,
            'shares': int(post['shares']) if not pd.isna(post['shares']) else 0,
            'is_premium': bool(post['is_premium']),
            'tags': json.loads(post['tags']) if post['tags'] else []
        })

    return jsonify(posts_data)

@app.route('/api/analytics/<publication_name>')
def api_analytics(publication_name):
    """Get analytics data."""
    days_back = request.args.get('days', 30, type=int)
    
    # Get basic analytics
    engagement = analytics_app.analytics.get_engagement_metrics(publication_name, days_back)
    growth = analytics_app.analytics.get_growth_metrics(publication_name, days_back)
    insights = analytics_app.analytics.get_content_insights(publication_name, days_back)
    
    return jsonify({
        'engagement': engagement,
        'growth': growth,
        'insights': insights
    })

@app.route('/api/scrape', methods=['POST'])
def api_scrape():
    """Scrape a new publication."""
    data = request.get_json()
    publication_name = data.get('publication_name')
    max_posts = data.get('max_posts', 100)
    
    if not publication_name:
        return jsonify({'error': 'Publication name required'}), 400
    
    try:
        result = analytics_app.scrape_publication(publication_name, max_posts)
        return jsonify(result)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/export/<publication_name>')
def api_export(publication_name):
    """Export data as JSON."""
    try:
        export_data = analytics_app.analytics.get_export_data(publication_name)
        return jsonify(export_data)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/export/<publication_name>/csv')
def api_export_csv(publication_name):
    """Export data as CSV."""
    try:
        collector = analytics_app.get_collector(publication_name)
        if not collector:
            return jsonify({'error': 'Publication not found'}), 404

        filename = f"{publication_name}_analytics_{datetime.now().strftime('%Y%m%d')}"
        collector.export_to_csv(filename)
        return send_file(f"{filename}_posts.csv", as_attachment=True)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/dashboard/<publication_name>')
def publication_dashboard(publication_name):
    """Individual publication dashboard."""
    publication_data = analytics_app.get_publication_data(publication_name)
    if not publication_data:
        return "Publication not found", 404
    
    return render_template('publication.html', 
                         publication_name=publication_name,
                         publication_data=publication_data)

def main():
    """Main function to run the application."""
    print("Starting Substack Analytics Dashboard...")
    print("Dashboard will be available at: http://localhost:5000")
    print("You can analyze any Substack publication by entering its name")
    print("Features include: Web scraping, Analytics, Charts, Export functionality")
    print("\n" + "="*60)
    
    # Create necessary directories
    os.makedirs('templates', exist_ok=True)
    os.makedirs('static', exist_ok=True)
    
    # Initialize database tables
    print("Initializing database...")
    # Database is already initialized in the analytics class constructor
    print("Database initialized successfully!")
    
    # Run the Flask app
    app.run(debug=True, host='0.0.0.0', port=5000)

if __name__ == '__main__':
    main()
