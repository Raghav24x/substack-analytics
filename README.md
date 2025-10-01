# Substack Analytics Dashboard

A comprehensive web scraping and analytics dashboard for Substack publications. This tool allows you to analyze any Substack publication's performance, content trends, and engagement metrics.

## Features

### 🔍 **Web Scraping**
- Scrape posts, metadata, and analytics from any Substack publication
- Advanced HTML parsing with BeautifulSoup
- Rate limiting and error handling
- Support for both free and premium content detection

### 📊 **Analytics Dashboard**
- Interactive web interface with modern UI
- Real-time charts and visualizations
- Comprehensive metrics and insights
- Publication comparison tools

### 📈 **Data Analysis**
- **Engagement Metrics**: Word count, read time, posting frequency
- **Growth Analysis**: Content trends over time, growth rates
- **Content Insights**: Top tags, common words, performance analysis
- **Publishing Patterns**: Best posting times, content length analysis

### 💾 **Data Storage**
- SQLite database for persistent storage
- Structured data models for posts and publications
- Easy data export and import

### 📤 **Export Functionality**
- Export data as CSV or JSON
- Comprehensive analytics reports
- Custom date range exports

## Installation

1. **Clone or download the project files**

2. **Install Python dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

3. **Run the application:**
   ```bash
   python main.py
   ```

4. **Open your browser and go to:**
   ```
   http://localhost:5000
   ```
   
## Deployment on Render

To ensure Render uses the correct Python version, add a file named `runtime.txt` to the root of your repository with the following content:

```
python-3.11.8
```

This instructs Render to use Python 3.11.8, which is compatible with all dependencies in this project.  
If you do not specify this file, Render may use the latest Python version (such as 3.13), which can result in build failures.

## Usage

### Basic Usage

1. **Add a Publication:**
   - Enter the Substack publication name (e.g., "platformer" for platformer.substack.com)
   - Set the maximum number of posts to scrape
   - Click "Start Scraping"

2. **View Analytics:**
   - The dashboard will automatically load after scraping
   - View comprehensive metrics and charts
   - Analyze posting patterns and content performance

3. **Export Data:**
   - Use the export buttons to download data as CSV or JSON
   - Access detailed analytics reports

### Advanced Features

#### Analytics Metrics

- **Total Posts**: Number of posts scraped
- **Total Words**: Combined word count of all posts
- **Average Read Time**: Estimated reading time per post
- **Premium Posts**: Number of subscriber-only content
- **Posting Patterns**: Best days and times to post
- **Content Analysis**: Most common words and tags

#### Growth Analysis

- **Daily/Weekly Metrics**: Posts and word count trends
- **Growth Rates**: Content production growth over time
- **Performance Comparison**: High vs low performing posts

#### Content Insights

- **Title Analysis**: Optimal title length recommendations
- **Word Count Distribution**: Content length patterns
- **Tag Analysis**: Most popular content categories
- **Recommendations**: AI-powered content suggestions

## File Structure

```
substack_analytics/
├── main.py                 # Main Flask application
├── enhanced_collector.py   # Web scraping engine
├── analytics.py           # Analytics and metrics calculation
├── dashboard.py           # Dashboard routes and API
├── requirements.txt       # Python dependencies
├── templates/
│   └── index.html        # Main dashboard template
├── static/               # CSS, JS, and other static files
└── substack_analytics.db # SQLite database (created automatically)
```

## API Endpoints

### Publications
- `GET /api/publications` - Get all tracked publications
- `GET /api/publication/<name>` - Get specific publication data
- `POST /api/scrape` - Scrape a new publication

### Posts
- `GET /api/posts/<name>` - Get posts for a publication
- `GET /api/posts/<name>?limit=50` - Limit number of posts

### Analytics
- `GET /api/analytics/<name>` - Get analytics data
- `GET /api/analytics/<name>?days=30` - Analytics for specific period

### Export
- `GET /api/export/<name>` - Export as JSON
- `GET /api/export/<name>/csv` - Export as CSV

## Examples

### Scraping a Publication

```python
from enhanced_collector import SubstackDataCollector

# Initialize collector
collector = SubstackDataCollector("platformer")

# Scrape publication info
publication_data = collector.scrape_publication_info()

# Scrape posts
posts = collector.scrape_posts(max_posts=100)

# Save to database
collector.save_to_database(posts, publication_data)
```

### Getting Analytics

```python
from analytics import SubstackAnalytics

# Initialize analytics
analytics = SubstackAnalytics()

# Get engagement metrics
engagement = analytics.get_engagement_metrics("platformer", days_back=30)

# Get growth metrics
growth = analytics.get_growth_metrics("platformer", days_back=90)

# Get content insights
insights = analytics.get_content_insights("platformer", days_back=30)
```

## Configuration

### Database
The application uses SQLite by default. The database file (`substack_analytics.db`) is created automatically.

### Rate Limiting
The scraper includes built-in rate limiting to be respectful to Substack servers. You can adjust the delay in `enhanced_collector.py`.

### Customization
- Modify `templates/index.html` for UI changes
- Update `analytics.py` for custom metrics
- Extend `enhanced_collector.py` for additional data sources

## Troubleshooting

### Common Issues

1. **Scraping fails**: Check if the publication name is correct and the site is accessible
2. **Database errors**: Ensure you have write permissions in the project directory
3. **Import errors**: Make sure all dependencies are installed with `pip install -r requirements.txt`

### Performance Tips

- Start with smaller post limits (10-50) for testing
- Use the database to avoid re-scraping the same data
- Export data regularly for backup

## Legal Considerations

- This tool is for educational and personal use
- Respect Substack's terms of service
- Use reasonable rate limiting
- Don't overload servers with excessive requests

## Contributing

Feel free to submit issues, feature requests, or pull requests to improve the tool.

## License

This project is open source and available under the MIT License.
