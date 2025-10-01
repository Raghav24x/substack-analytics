"""
Interactive dashboard using Dash for Substack analytics.
"""

import dash
from dash import dcc, html, Input, Output, callback
import dash_bootstrap_components as dbc
import plotly.graph_objects as go
from datetime import datetime, timedelta
import pandas as pd
from typing import Dict, Optional
import logging

from .data_collector import SubstackDataCollector
from .analytics_engine import SubstackAnalytics
from .visualization import SubstackVisualizer

class SubstackDashboard:
    """Interactive dashboard for Substack analytics."""
    
    def __init__(self, publication_name: str, api_key: Optional[str] = None):
        """
        Initialize the dashboard.
        
        Args:
            publication_name: Name of the Substack publication
            api_key: Optional API key for enhanced access
        """
        self.publication_name = publication_name
        self.api_key = api_key
        self.logger = logging.getLogger(__name__)
        
        # Initialize data collector and analytics
        self.data_collector = SubstackDataCollector(publication_name, api_key)
        self.analytics_data = None
        self.visualizer = None
        
        # Initialize Dash app
        self.app = dash.Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP])
        self.setup_layout()
        self.setup_callbacks()
    
    def setup_layout(self):
        """Set up the dashboard layout."""
        self.app.layout = dbc.Container([
            dbc.Row([
                dbc.Col([
                    html.H1(f"Substack Analytics Dashboard", className="text-center mb-4"),
                    html.H3(f"Publication: {self.publication_name}", className="text-center mb-4"),
                ])
            ]),
            
            dbc.Row([
                dbc.Col([
                    dbc.Card([
                        dbc.CardBody([
                            html.H4("Data Collection", className="card-title"),
                            dbc.Button("Refresh Data", id="refresh-button", color="primary", className="mb-3"),
                            html.Div(id="data-status"),
                            html.Div(id="last-updated")
                        ])
                    ])
                ], width=12)
            ], className="mb-4"),
            
            dbc.Row([
                dbc.Col([
                    dbc.Card([
                        dbc.CardBody([
                            html.H4("Publishing Frequency", className="card-title"),
                            dcc.Graph(id="publishing-frequency-chart")
                        ])
                    ])
                ], width=6),
                
                dbc.Col([
                    dbc.Card([
                        dbc.CardBody([
                            html.H4("Content Length Distribution", className="card-title"),
                            dcc.Graph(id="content-length-chart")
                        ])
                    ])
                ], width=6)
            ], className="mb-4"),
            
            dbc.Row([
                dbc.Col([
                    dbc.Card([
                        dbc.CardBody([
                            html.H4("Top Keywords", className="card-title"),
                            dcc.Graph(id="topics-chart")
                        ])
                    ])
                ], width=6),
                
                dbc.Col([
                    dbc.Card([
                        dbc.CardBody([
                            html.H4("Reading Time Analysis", className="card-title"),
                            dcc.Graph(id="reading-time-chart")
                        ])
                    ])
                ], width=6)
            ], className="mb-4"),
            
            dbc.Row([
                dbc.Col([
                    dbc.Card([
                        dbc.CardBody([
                            html.H4("Engagement Trends", className="card-title"),
                            dcc.Graph(id="engagement-chart")
                        ])
                    ])
                ], width=6),
                
                dbc.Col([
                    dbc.Card([
                        dbc.CardBody([
                            html.H4("Notes Activity", className="card-title"),
                            dcc.Graph(id="notes-chart")
                        ])
                    ])
                ], width=6)
            ], className="mb-4"),
            
            dbc.Row([
                dbc.Col([
                    dbc.Card([
                        dbc.CardBody([
                            html.H4("Performance Summary", className="card-title"),
                            html.Div(id="performance-summary")
                        ])
                    ])
                ], width=12)
            ])
            
        ], fluid=True)
    
    def setup_callbacks(self):
        """Set up dashboard callbacks."""
        
        @self.app.callback(
            [Output("data-status", "children"),
             Output("last-updated", "children"),
             Output("publishing-frequency-chart", "figure"),
             Output("content-length-chart", "figure"),
             Output("topics-chart", "figure"),
             Output("reading-time-chart", "figure"),
             Output("engagement-chart", "figure"),
             Output("notes-chart", "figure"),
             Output("performance-summary", "children")],
            [Input("refresh-button", "n_clicks")]
        )
        def update_dashboard(n_clicks):
            """Update all dashboard components when refresh button is clicked."""
            try:
                # Collect data
                self.analytics_data = self.data_collector.get_analytics_data()
                
                # Process analytics
                analytics = SubstackAnalytics(self.analytics_data)
                performance_data = analytics.get_performance_summary()
                
                # Initialize visualizer
                self.visualizer = SubstackVisualizer(performance_data)
                
                # Create charts
                publishing_fig = self.visualizer.create_publishing_frequency_chart()
                content_length_fig = self.visualizer.create_content_length_distribution()
                topics_fig = self.visualizer.create_topic_analysis_chart()
                reading_time_fig = self.visualizer.create_reading_time_analysis()
                engagement_fig = self.visualizer.create_engagement_trends()
                notes_fig = self.visualizer.create_notes_activity_chart()
                
                # Create performance summary
                summary = self.create_performance_summary_html(performance_data)
                
                # Status messages
                data_status = dbc.Alert("Data refreshed successfully!", color="success")
                last_updated = html.P(f"Last updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
                
                return (data_status, last_updated, publishing_fig, content_length_fig, 
                       topics_fig, reading_time_fig, engagement_fig, notes_fig, summary)
                
            except Exception as e:
                self.logger.error(f"Error updating dashboard: {e}")
                error_msg = dbc.Alert(f"Error refreshing data: {str(e)}", color="danger")
                empty_fig = go.Figure()
                return (error_msg, "", empty_fig, empty_fig, empty_fig, empty_fig, empty_fig, empty_fig, "")
    
    def create_performance_summary_html(self, performance_data: Dict) -> html.Div:
        """Create HTML summary of performance metrics."""
        if not performance_data:
            return html.Div("No data available")
        
        # Extract key metrics
        pub_freq = performance_data.get('publishing_frequency', {})
        content_analysis = performance_data.get('content_analysis', {})
        notes_analysis = performance_data.get('notes_analysis', {})
        
        return html.Div([
            dbc.Row([
                dbc.Col([
                    html.H5("Publishing Metrics"),
                    html.P(f"Total Posts: {pub_freq.get('total_posts', 'N/A')}"),
                    html.P(f"Posts per Week: {pub_freq.get('posts_per_week', 'N/A'):.1f}"),
                    html.P(f"Most Active Day: {pub_freq.get('most_active_day', 'N/A')}"),
                ], width=4),
                
                dbc.Col([
                    html.H5("Content Metrics"),
                    html.P(f"Average Word Count: {content_analysis.get('average_word_count', 'N/A'):.0f}"),
                    html.P(f"Average Reading Time: {content_analysis.get('average_reading_time', 'N/A'):.1f} minutes"),
                    html.P(f"Total Words Published: {content_analysis.get('total_words_published', 'N/A'):,}"),
                ], width=4),
                
                dbc.Col([
                    html.H5("Notes Metrics"),
                    html.P(f"Total Notes: {notes_analysis.get('total_notes', 'N/A')}"),
                    html.P(f"Average Note Length: {notes_analysis.get('average_note_length', 'N/A'):.0f} words"),
                    html.P(f"Notes per Day: {notes_analysis.get('notes_per_day', 'N/A'):.1f}"),
                ], width=4)
            ])
        ])
    
    def run(self, debug: bool = True, port: int = 8050):
        """Run the dashboard."""
        self.logger.info(f"Starting dashboard for {self.publication_name}")
        self.app.run_server(debug=debug, port=port)
