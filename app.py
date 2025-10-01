from flask import Flask, render_template, jsonify, request
import sqlite3
import pandas as pd
import json
from datetime import datetime
import os
from enhanced_collector import SubstackDataCollector

app = Flask(__name__)

class AnalyticsDashboard:
    def __init__(self, db_path="substack_analytics.db"):
        self.db_path = db_path
        self.collectors = {}
    
    def add_publication(self, publication_name):
        collector = SubstackDataCollector(publication_name, self.db_path)
        self.collectors[publication_name] = collector
        return collector
    
    def get_publications(self):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT DISTINCT name FROM publication")
        publications = [row[0] for row in cursor.fetchall()]
        conn.close()
        return publications
    
    def scrape_publication(self, publication_name, max_posts=100):
        collector = self.add_publication(publication_name)
        publication_data = collector.scrape_publication_info()
        posts = collector.scrape_posts(max_posts)
        collector.save_to_database(posts, publication_data)
        return {'status': 'success', 'posts_count': len(posts)}

dashboard = AnalyticsDashboard()

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/scrape', methods=['POST'])
def api_scrape():
    data = request.get_json()
    publication_name = data.get('publication_name')
    max_posts = data.get('max_posts', 100)
    
    if not publication_name:
        return jsonify({'error': 'Publication name required'}), 400
    
    try:
        result = dashboard.scrape_publication(publication_name, max_posts)
        return jsonify(result)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    os.makedirs('templates', exist_ok=True)
    app.run(debug=True, host='0.0.0.0', port=5000)
