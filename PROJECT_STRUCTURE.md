# Substack Analytics Dashboard - Project Structure

## 📁 Project Files

```
substack_analytics/
├── 📄 main.py                    # Main Flask application entry point
├── 📄 enhanced_collector.py      # Advanced web scraping engine
├── 📄 analytics.py               # Analytics and metrics calculation
├── 📄 data_collector.py          # Original data collector (legacy)
├── 📄 dashboard.py               # Dashboard routes and API
├── 📄 app.py                     # Simple Flask app
├── 📄 example.py                 # Example usage script
├── 📄 scheduler.py               # Automated scheduling system
├── 📄 setup.py                   # Python package setup
├── 📄 install.bat                # Windows installation script
├── 📄 requirements.txt           # Python dependencies
├── 📄 README.md                  # Comprehensive documentation
├── 📄 PROJECT_STRUCTURE.md       # This file
├── 📄 .gitignore                 # Git ignore rules
├── 📁 templates/                 # HTML templates
│   └── 📄 index.html             # Main dashboard template
├── 📁 static/                    # Static files (CSS, JS, images)
└── 📁 __pycache__/               # Python cache files
```

## 🚀 Quick Start

### Windows:
1. Double-click `install.bat` to install dependencies
2. Run `python main.py`
3. Open http://localhost:5000

### Manual Installation:
1. `pip install -r requirements.txt`
2. `python main.py`
3. Open http://localhost:5000

## 📊 Features

- **Web Scraping**: Scrape any Substack publication
- **Analytics Dashboard**: Interactive charts and metrics
- **Data Export**: CSV and JSON export functionality
- **Real-time Monitoring**: Automated data collection
- **Content Analysis**: AI-powered insights and recommendations

## 🔧 Dependencies

- Flask 2.3.3
- requests 2.31.0
- beautifulsoup4 4.12.2
- pandas 2.1.1
- lxml 4.9.3
- selenium 4.15.0
- webdriver-manager 4.0.1
- python-3.11.8

## 📝 Usage

1. Enter publication name (e.g., "platformer")
2. Set max posts to scrape
3. Click "Start Scraping"
4. View analytics and insights
5. Export data as needed

## 🛠️ Development

- Main application: `main.py`
- Web scraping: `enhanced_collector.py`
- Analytics: `analytics.py`
- Templates: `templates/index.html`

