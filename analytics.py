"""
Advanced analytics module for Substack data.
Provides comprehensive metrics and insights.
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
import sqlite3
import json
from collections import Counter
import re

class SubstackAnalytics:
    """Advanced analytics engine for Substack publications."""
    
    def __init__(self, db_path: str = "substack_analytics.db"):
        self.db_path = db_path
        self._init_database()
    
    def _init_database(self):
        """Initialize SQLite database with required tables."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Create posts table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS posts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                slug TEXT UNIQUE,
                url TEXT UNIQUE,
                content TEXT,
                excerpt TEXT,
                author TEXT,
                published_at TIMESTAMP,
                updated_at TIMESTAMP,
                word_count INTEGER,
                read_time INTEGER,
                likes INTEGER DEFAULT 0,
                comments INTEGER DEFAULT 0,
                shares INTEGER DEFAULT 0,
                tags TEXT,
                is_premium BOOLEAN DEFAULT 0,
                subscriber_only BOOLEAN DEFAULT 0,
                scraped_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Create publication table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS publication (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT,
                description TEXT,
                url TEXT,
                subscriber_count INTEGER,
                posts_count INTEGER,
                founded_date TIMESTAMP,
                author TEXT,
                social_links TEXT,
                revenue_estimate REAL,
                last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Create analytics table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS analytics (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                date DATE,
                metric_name TEXT,
                metric_value REAL,
                publication_name TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        conn.commit()
        conn.close()
    
    def get_engagement_metrics(self, publication_name: str, days_back: int = 30) -> Dict:
        """Calculate engagement metrics for a publication."""
        conn = sqlite3.connect(self.db_path)
        
        # Get posts from the specified period
        start_date = datetime.now() - timedelta(days=days_back)
        query = '''
            SELECT * FROM posts 
            WHERE url LIKE ? AND published_at >= ?
            ORDER BY published_at DESC
        '''
        
        posts_df = pd.read_sql_query(query, conn, params=(f"%{publication_name}%", start_date))
        conn.close()
        
        if posts_df.empty:
            return {}
        
        # Calculate metrics
        total_posts = len(posts_df)
        total_words = posts_df['word_count'].sum()
        avg_word_count = posts_df['word_count'].mean()
        avg_read_time = posts_df['read_time'].mean()
        
        # Content frequency
        posts_df['published_at'] = pd.to_datetime(posts_df['published_at'])
        posts_df['weekday'] = posts_df['published_at'].dt.day_name()
        posts_df['hour'] = posts_df['published_at'].dt.hour

        # Publishing patterns
        weekday_distribution = posts_df['weekday'].value_counts().to_dict()
        hour_distribution = posts_df['hour'].value_counts().to_dict()

        # Content analysis
        premium_posts = len(posts_df[posts_df['is_premium'] == 1])
        free_posts = len(posts_df[posts_df['is_premium'] == 0])

        def aggregate_engagement(series: Optional[pd.Series]) -> Tuple[int, float]:
            if series is None or series.empty:
                return 0, 0.0

            numeric = pd.to_numeric(series.fillna(0), errors='coerce').fillna(0)
            total = int(numeric.sum())
            average = float(numeric.mean()) if len(numeric) else 0.0
            return total, round(average, 1)

        total_likes, avg_likes = aggregate_engagement(posts_df.get('likes'))
        total_comments, avg_comments = aggregate_engagement(posts_df.get('comments'))
        total_shares, avg_shares = aggregate_engagement(posts_df.get('shares'))

        # Tag analysis
        all_tags = []
        for tags_json in posts_df['tags']:
            if tags_json:
                tags = json.loads(tags_json)
                all_tags.extend(tags)
        
        top_tags = Counter(all_tags).most_common(10)
        
        # Word count analysis
        word_count_stats = {
            'min': posts_df['word_count'].min(),
            'max': posts_df['word_count'].max(),
            'median': posts_df['word_count'].median(),
            'std': posts_df['word_count'].std()
        }
        
        # Read time analysis
        read_time_stats = {
            'min': posts_df['read_time'].min(),
            'max': posts_df['read_time'].max(),
            'median': posts_df['read_time'].median(),
            'std': posts_df['read_time'].std()
        }
        
        return {
            'total_posts': total_posts,
            'total_words': int(total_words),
            'avg_word_count': round(avg_word_count, 1),
            'avg_read_time': round(avg_read_time, 1),
            'premium_posts': premium_posts,
            'free_posts': free_posts,
            'premium_ratio': round(premium_posts / total_posts * 100, 1) if total_posts > 0 else 0,
            'total_likes': total_likes,
            'avg_likes': avg_likes,
            'total_comments': total_comments,
            'avg_comments': avg_comments,
            'total_shares': total_shares,
            'avg_shares': avg_shares,
            'weekday_distribution': weekday_distribution,
            'hour_distribution': hour_distribution,
            'top_tags': top_tags,
            'word_count_stats': word_count_stats,
            'read_time_stats': read_time_stats
        }
    
    def get_growth_metrics(self, publication_name: str, days_back: int = 90) -> Dict:
        """Calculate growth metrics over time."""
        conn = sqlite3.connect(self.db_path)
        
        start_date = datetime.now() - timedelta(days=days_back)
        query = '''
            SELECT published_at, word_count, is_premium FROM posts 
            WHERE url LIKE ? AND published_at >= ?
            ORDER BY published_at ASC
        '''
        
        posts_df = pd.read_sql_query(query, conn, params=(f"%{publication_name}%", start_date))
        conn.close()
        
        if posts_df.empty:
            return {}
        
        posts_df['published_at'] = pd.to_datetime(posts_df['published_at'])
        posts_df['date'] = posts_df['published_at'].dt.date
        
        # Daily metrics
        daily_metrics = posts_df.groupby('date').agg({
            'word_count': ['count', 'sum', 'mean'],
            'is_premium': 'sum'
        }).round(2)
        
        daily_metrics.columns = ['posts_count', 'total_words', 'avg_words', 'premium_posts']
        daily_metrics = daily_metrics.reset_index()
        
        # Weekly metrics
        posts_df['week'] = posts_df['published_at'].dt.to_period('W')
        weekly_metrics = posts_df.groupby('week').agg({
            'word_count': ['count', 'sum', 'mean'],
            'is_premium': 'sum'
        }).round(2)
        
        weekly_metrics.columns = ['posts_count', 'total_words', 'avg_words', 'premium_posts']
        weekly_metrics = weekly_metrics.reset_index()
        
        # Calculate growth rates
        if len(daily_metrics) > 1:
            posts_growth = self._calculate_growth_rate(daily_metrics['posts_count'].tolist())
            words_growth = self._calculate_growth_rate(daily_metrics['total_words'].tolist())
        else:
            posts_growth = words_growth = 0
        
        return {
            'daily_metrics': daily_metrics.to_dict('records'),
            'weekly_metrics': weekly_metrics.to_dict('records'),
            'posts_growth_rate': round(posts_growth, 2),
            'words_growth_rate': round(words_growth, 2),
            'total_days': len(daily_metrics),
            'avg_posts_per_day': round(daily_metrics['posts_count'].mean(), 2),
            'avg_words_per_day': round(daily_metrics['total_words'].mean(), 2)
        }
    
    def _calculate_growth_rate(self, values: List[float]) -> float:
        """Calculate growth rate between first and last values."""
        if len(values) < 2:
            return 0
        
        first_value = values[0]
        last_value = values[-1]
        
        if first_value == 0:
            return 0
        
        return ((last_value - first_value) / first_value) * 100
    
    def get_content_insights(self, publication_name: str, days_back: int = 30) -> Dict:
        """Generate content insights and recommendations."""
        conn = sqlite3.connect(self.db_path)
        
        start_date = datetime.now() - timedelta(days=days_back)
        query = '''
            SELECT title, content, word_count, read_time, is_premium, published_at, tags
            FROM posts 
            WHERE url LIKE ? AND published_at >= ?
            ORDER BY published_at DESC
        '''
        
        posts_df = pd.read_sql_query(query, conn, params=(f"%{publication_name}%", start_date))
        conn.close()
        
        if posts_df.empty:
            return {}
        
        # Title analysis
        titles = posts_df['title'].tolist()
        title_lengths = [len(title) for title in titles]
        
        # Content analysis
        contents = posts_df['content'].fillna('').tolist()
        
        # Extract common words (excluding common stop words)
        stop_words = {'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 'by', 'is', 'are', 'was', 'were', 'be', 'been', 'have', 'has', 'had', 'do', 'does', 'did', 'will', 'would', 'could', 'should', 'may', 'might', 'must', 'can', 'this', 'that', 'these', 'those', 'i', 'you', 'he', 'she', 'it', 'we', 'they', 'me', 'him', 'her', 'us', 'them'}
        
        all_words = []
        for content in contents:
            words = re.findall(r'\b[a-zA-Z]+\b', content.lower())
            all_words.extend([word for word in words if word not in stop_words and len(word) > 3])
        
        common_words = Counter(all_words).most_common(20)
        
        # Performance analysis
        high_performing_posts = posts_df.nlargest(5, 'word_count')
        low_performing_posts = posts_df.nsmallest(5, 'word_count')
        
        # Recommendations
        recommendations = self._generate_recommendations(posts_df, common_words)
        
        return {
            'title_analysis': {
                'avg_length': round(np.mean(title_lengths), 1),
                'min_length': min(title_lengths),
                'max_length': max(title_lengths),
                'recommended_length': 50  # Optimal title length
            },
            'common_words': common_words,
            'high_performing_posts': high_performing_posts[['title', 'word_count', 'read_time']].to_dict('records'),
            'low_performing_posts': low_performing_posts[['title', 'word_count', 'read_time']].to_dict('records'),
            'recommendations': recommendations
        }
    
    def _generate_recommendations(self, posts_df: pd.DataFrame, common_words: List[Tuple[str, int]]) -> List[str]:
        """Generate content recommendations based on analysis."""
        recommendations = []
        
        # Check posting frequency
        posts_df['published_at'] = pd.to_datetime(posts_df['published_at'])
        days_since_last_post = (datetime.now() - posts_df['published_at'].max()).days
        
        if days_since_last_post > 7:
            recommendations.append(f"Consider posting more frequently. Last post was {days_since_last_post} days ago.")
        
        # Check word count consistency
        word_count_std = posts_df['word_count'].std()
        word_count_mean = posts_df['word_count'].mean()
        
        if word_count_std > word_count_mean * 0.5:
            recommendations.append("Consider maintaining more consistent post lengths for better reader engagement.")
        
        # Check premium content ratio
        premium_ratio = len(posts_df[posts_df['is_premium'] == 1]) / len(posts_df) * 100
        if premium_ratio < 20:
            recommendations.append("Consider creating more premium content to increase revenue potential.")
        elif premium_ratio > 80:
            recommendations.append("Consider balancing premium and free content to maintain audience growth.")
        
        # Check read time
        avg_read_time = posts_df['read_time'].mean()
        if avg_read_time < 3:
            recommendations.append("Consider creating longer-form content for better engagement.")
        elif avg_read_time > 15:
            recommendations.append("Consider breaking down very long posts into series for better readability.")
        
        return recommendations
    
    def get_export_data(self, publication_name: str, format: str = 'json') -> Dict:
        """Export comprehensive data for a publication."""
        conn = sqlite3.connect(self.db_path)
        
        # Get all posts
        posts_query = '''
            SELECT * FROM posts 
            WHERE url LIKE ?
            ORDER BY published_at DESC
        '''
        posts_df = pd.read_sql_query(posts_query, conn, params=(f"%{publication_name}%",))
        
        # Get publication info
        pub_query = 'SELECT * FROM publication WHERE name = ?'
        pub_df = pd.read_sql_query(pub_query, conn, params=(publication_name,))
        
        conn.close()
        
        # Get analytics
        engagement = self.get_engagement_metrics(publication_name)
        growth = self.get_growth_metrics(publication_name)
        insights = self.get_content_insights(publication_name)
        
        export_data = {
            'publication_info': pub_df.to_dict('records')[0] if not pub_df.empty else {},
            'posts': posts_df.to_dict('records'),
            'analytics': {
                'engagement': engagement,
                'growth': growth,
                'insights': insights
            },
            'exported_at': datetime.now().isoformat()
        }
        
        return export_data
