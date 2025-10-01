"""
Advanced data collection module for Substack publications.
Handles comprehensive web scraping of posts, notes, and analytics data.
"""

import requests
import json
import time
import re
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
import logging
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
import sqlite3
import pandas as pd
from dataclasses import dataclass, asdict
import random

@dataclass
class PostData:
    """Data class for post information."""
    title: str
    slug: str
    url: str
    content: str
    excerpt: str
    author: str
    published_at: datetime
    updated_at: datetime
    word_count: int
    read_time: int
    likes: int
    comments: int
    shares: int
    tags: List[str]
    is_premium: bool
    subscriber_only: bool

@dataclass
class PublicationData:
    """Data class for publication information."""
    name: str
    description: str
    url: str
    subscriber_count: int
    posts_count: int
    founded_date: datetime
    author: str
    social_links: Dict[str, str]
    revenue_estimate: Optional[float]

class SubstackDataCollector:
    """Advanced web scraper for Substack publications."""
    
    def __init__(self, publication_name: str, db_path: str = "substack_analytics.db"):
        """
        Initialize the data collector.
        
        Args:
            publication_name: The name of the Substack publication
            db_path: Path to SQLite database file
        """
        self.publication_name = publication_name
        self.base_url = f"https://{publication_name}.substack.com"
        self.db_path = db_path
        
        # Set up logging
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger(__name__)
        
        # Initialize database
        self._init_database()
        
        # Session for persistent connections
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
        })
    
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
    
    def _get_page_content(self, url: str) -> str:
        """Get page content using requests."""
        try:
            response = self.session.get(url, timeout=30)
            response.raise_for_status()
            return response.text
        except Exception as e:
            self.logger.error(f"Request error for {url}: {e}")
            return ""
    
    def scrape_publication_info(self) -> PublicationData:
        """Scrape publication information from the main page."""
        try:
            content = self._get_page_content(self.base_url)
            soup = BeautifulSoup(content, 'html.parser')
            
            # Extract publication name
            name = soup.find('h1', class_='publication-title') or soup.find('title')
            name = name.get_text(strip=True) if name else self.publication_name
            
            # Extract description
            description = ""
            desc_elem = soup.find('meta', {'name': 'description'})
            if desc_elem:
                description = desc_elem.get('content', '')
            
            # Extract author
            author = ""
            author_elem = soup.find('div', class_='author-name') or soup.find('span', class_='author')
            if author_elem:
                author = author_elem.get_text(strip=True)
            
            # Extract social links
            social_links = {}
            social_elements = soup.find_all('a', href=re.compile(r'(twitter|linkedin|facebook|instagram)'))
            for link in social_elements:
                href = link.get('href', '')
                if 'twitter' in href:
                    social_links['twitter'] = href
                elif 'linkedin' in href:
                    social_links['linkedin'] = href
                elif 'facebook' in href:
                    social_links['facebook'] = href
                elif 'instagram' in href:
                    social_links['instagram'] = href
            
            # Estimate subscriber count
            subscriber_count = self._estimate_subscriber_count(soup)
            
            return PublicationData(
                name=name,
                description=description,
                url=self.base_url,
                subscriber_count=subscriber_count,
                posts_count=0,
                founded_date=datetime.now(),
                author=author,
                social_links=social_links,
                revenue_estimate=None
            )
            
        except Exception as e:
            self.logger.error(f"Error scraping publication info: {e}")
            return PublicationData(
                name=self.publication_name,
                description="",
                url=self.base_url,
                subscriber_count=0,
                posts_count=0,
                founded_date=datetime.now(),
                author="",
                social_links={},
                revenue_estimate=None
            )
    
    def _estimate_subscriber_count(self, soup: BeautifulSoup) -> int:
        """Estimate subscriber count from available data."""
        subscriber_text = soup.find_all(text=re.compile(r'\d+.*subscriber'))
        for text in subscriber_text:
            numbers = re.findall(r'\d+', text)
            if numbers:
                return int(numbers[0])
        return 0
    
    def scrape_posts(self, max_posts: int = 100) -> List[PostData]:
        """Scrape posts from the publication."""
        posts = []
        page = 1
        
        while len(posts) < max_posts:
            try:
                # Try different URL patterns for posts
                urls_to_try = [
                    f"{self.base_url}/archive?page={page}",
                    f"{self.base_url}/p?page={page}",
                    f"{self.base_url}/?page={page}"
                ]
                
                content = ""
                for url in urls_to_try:
                    content = self._get_page_content(url)
                    if content and "post" in content.lower():
                        break
                
                if not content:
                    break
                
                soup = BeautifulSoup(content, 'html.parser')
                post_elements = self._find_post_elements(soup)
                
                if not post_elements:
                    break
                
                for element in post_elements:
                    if len(posts) >= max_posts:
                        break
                    
                    post_data = self._extract_post_data(element)
                    if post_data:
                        posts.append(post_data)
                
                page += 1
                time.sleep(random.uniform(1, 3))  # Rate limiting
                
            except Exception as e:
                self.logger.error(f"Error scraping posts page {page}: {e}")
                break
        
        return posts[:max_posts]
    
    def _find_post_elements(self, soup: BeautifulSoup) -> List:
        """Find post elements in the page."""
        selectors = [
            'article.post',
            'div.post',
            'div[data-testid="post"]',
            'a[href*="/p/"]',
            '.post-preview',
            '.post-item'
        ]
        
        for selector in selectors:
            elements = soup.select(selector)
            if elements:
                return elements
        
        return []
    
    def _extract_post_data(self, element) -> Optional[PostData]:
        """Extract post data from a post element."""
        try:
            # Extract title
            title_elem = element.find('h1') or element.find('h2') or element.find('h3')
            title = title_elem.get_text(strip=True) if title_elem else ""
            
            # Extract URL
            link_elem = element.find('a', href=True)
            if not link_elem:
                return None
            
            url = urljoin(self.base_url, link_elem['href'])
            slug = url.split('/')[-1] if url else ""
            
            # Extract excerpt
            excerpt_elem = element.find('p') or element.find('div', class_='excerpt')
            excerpt = excerpt_elem.get_text(strip=True) if excerpt_elem else ""
            
            # Extract author
            author_elem = element.find('span', class_='author') or element.find('div', class_='author')
            author = author_elem.get_text(strip=True) if author_elem else ""
            
            # Extract published date
            date_elem = element.find('time') or element.find('span', class_='date')
            published_at = datetime.now()
            if date_elem:
                date_text = date_elem.get_text(strip=True)
                published_at = self._parse_date(date_text)
            
            # Check if premium/subscriber only
            is_premium = 'premium' in element.get('class', []) or 'subscriber' in element.get_text().lower()
            subscriber_only = 'subscriber' in element.get_text().lower()
            
            # Extract tags
            tags = []
            tag_elements = element.find_all('span', class_='tag') or element.find_all('a', class_='tag')
            for tag_elem in tag_elements:
                tags.append(tag_elem.get_text(strip=True))
            
            # Get full content if possible
            content = self._scrape_post_content(url)
            word_count = len(content.split()) if content else 0
            read_time = max(1, word_count // 200)  # Estimate reading time
            
            return PostData(
                title=title,
                slug=slug,
                url=url,
                content=content,
                excerpt=excerpt,
                author=author,
                published_at=published_at,
                updated_at=published_at,
                word_count=word_count,
                read_time=read_time,
                likes=0,
                comments=0,
                shares=0,
                tags=tags,
                is_premium=is_premium,
                subscriber_only=subscriber_only
            )
            
        except Exception as e:
            self.logger.error(f"Error extracting post data: {e}")
            return None
    
    def _scrape_post_content(self, url: str) -> str:
        """Scrape full content of a post."""
        try:
            content = self._get_page_content(url)
            soup = BeautifulSoup(content, 'html.parser')
            
            # Find main content area
            content_selectors = [
                'div.post-content',
                'article .content',
                'div[data-testid="post-content"]',
                '.post-body'
            ]
            
            for selector in content_selectors:
                content_elem = soup.select_one(selector)
                if content_elem:
                    return content_elem.get_text(strip=True)
            
            return ""
            
        except Exception as e:
            self.logger.error(f"Error scraping post content from {url}: {e}")
            return ""
    
    def _parse_date(self, date_text: str) -> datetime:
        """Parse date string to datetime object."""
        try:
            formats = [
                '%B %d, %Y',
                '%b %d, %Y',
                '%Y-%m-%d',
                '%m/%d/%Y',
                '%d/%m/%Y'
            ]
            
            for fmt in formats:
                try:
                    return datetime.strptime(date_text, fmt)
                except ValueError:
                    continue
            
            return datetime.now()
            
        except Exception:
            return datetime.now()
    
    def save_to_database(self, posts: List[PostData], publication: PublicationData):
        """Save scraped data to database."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            # Save publication data
            cursor.execute('''
                INSERT OR REPLACE INTO publication 
                (name, description, url, subscriber_count, posts_count, founded_date, author, social_links, revenue_estimate)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                publication.name,
                publication.description,
                publication.url,
                publication.subscriber_count,
                len(posts),
                publication.founded_date,
                publication.author,
                json.dumps(publication.social_links),
                publication.revenue_estimate
            ))
            
            # Save posts data
            for post in posts:
                cursor.execute('''
                    INSERT OR REPLACE INTO posts 
                    (title, slug, url, content, excerpt, author, published_at, updated_at, 
                     word_count, read_time, likes, comments, shares, tags, is_premium, subscriber_only)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    post.title,
                    post.slug,
                    post.url,
                    post.content,
                    post.excerpt,
                    post.author,
                    post.published_at,
                    post.updated_at,
                    post.word_count,
                    post.read_time,
                    post.likes,
                    post.comments,
                    post.shares,
                    json.dumps(post.tags),
                    post.is_premium,
                    post.subscriber_only
                ))
            
            conn.commit()
            self.logger.info(f"Saved {len(posts)} posts to database")
            
        except Exception as e:
            self.logger.error(f"Error saving to database: {e}")
            conn.rollback()
        finally:
            conn.close()
    
    def get_analytics_data(self, days_back: int = 30) -> Dict:
        """Get comprehensive analytics data."""
        conn = sqlite3.connect(self.db_path)
        
        # Get posts from the last N days
        start_date = datetime.now() - timedelta(days=days_back)
        
        query = '''
            SELECT * FROM posts 
            WHERE published_at >= ? 
            ORDER BY published_at DESC
        '''
        
        posts_df = pd.read_sql_query(query, conn, params=(start_date,))
        
        # Calculate analytics
        analytics = {
            'publication_name': self.publication_name,
            'period_days': days_back,
            'total_posts': len(posts_df),
            'total_words': posts_df['word_count'].sum() if not posts_df.empty else 0,
            'avg_read_time': posts_df['read_time'].mean() if not posts_df.empty else 0,
            'premium_posts': len(posts_df[posts_df['is_premium'] == 1]) if not posts_df.empty else 0,
            'posts_by_month': self._get_posts_by_month(posts_df),
            'top_tags': self._get_top_tags(posts_df),
            'word_count_distribution': posts_df['word_count'].tolist() if not posts_df.empty else [],
            'posts_timeline': self._get_posts_timeline(posts_df)
        }
        
        conn.close()
        return analytics
    
    def _get_posts_by_month(self, posts_df: pd.DataFrame) -> Dict:
        """Get posts count by month."""
        if posts_df.empty:
            return {}
        
        posts_df['month'] = pd.to_datetime(posts_df['published_at']).dt.to_period('M')
        return posts_df['month'].value_counts().to_dict()
    
    def _get_top_tags(self, posts_df: pd.DataFrame) -> List[Tuple[str, int]]:
        """Get top tags from posts."""
        if posts_df.empty:
            return []
        
        all_tags = []
        for tags_json in posts_df['tags']:
            if tags_json:
                tags = json.loads(tags_json)
                all_tags.extend(tags)
        
        from collections import Counter
        return Counter(all_tags).most_common(10)
    
    def _get_posts_timeline(self, posts_df: pd.DataFrame) -> List[Dict]:
        """Get posts timeline data."""
        if posts_df.empty:
            return []
        
        timeline = []
        for _, post in posts_df.iterrows():
            timeline.append({
                'date': post['published_at'],
                'title': post['title'],
                'word_count': post['word_count'],
                'read_time': post['read_time'],
                'is_premium': bool(post['is_premium'])
            })
        
        return timeline
    
    def export_to_csv(self, filename: str = None):
        """Export data to CSV files."""
        if not filename:
            filename = f"{self.publication_name}_analytics_{datetime.now().strftime('%Y%m%d')}"
        
        conn = sqlite3.connect(self.db_path)
        
        # Export posts
        posts_df = pd.read_sql_query("SELECT * FROM posts", conn)
        posts_df.to_csv(f"{filename}_posts.csv", index=False)
        
        # Export publication data
        pub_df = pd.read_sql_query("SELECT * FROM publication", conn)
        pub_df.to_csv(f"{filename}_publication.csv", index=False)
        
        conn.close()
        self.logger.info(f"Data exported to {filename}_*.csv")
    
    def close(self):
        """Close resources."""
        self.session.close()
