from flask import Flask, render_template, jsonify, request
from pymongo import MongoClient
import logging
from logging.handlers import RotatingFileHandler
import os
from datetime import datetime
import plotly.express as px
import plotly.graph_objects as go
import json
import time
import pandas as pd

# Create app
app = Flask(__name__)

# Ensure logs directory exists
if not os.path.exists('logs'):
    os.makedirs('logs')

# Configure logging
handler = RotatingFileHandler('logs/app.log', maxBytes=10000, backupCount=3)
handler.setFormatter(logging.Formatter(
    '%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]'
))
handler.setLevel(logging.INFO)
app.logger.addHandler(handler)
app.logger.setLevel(logging.INFO)
app.logger.info('Dashboard startup')

# MongoDB connection with error handling
try:
    client = MongoClient('mongodb://localhost:27017/')
    db = client['reddit_crawler']
    db_chan = client['chan_crawler']
    # Test connection
    client.server_info()
    app.logger.info('MongoDB connection successful')
except Exception as e:
    app.logger.error(f'MongoDB connection failed: {str(e)}')

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/volume_comparison', methods=['POST'])
def volume_comparison():
    try:
        start_time = time.time()
        app.logger.info('Starting volume comparison analysis')
        
        data = request.json
        start_date = datetime.strptime(data['start_date'], '%Y-%m-%d')
        end_date = datetime.strptime(data['end_date'], '%Y-%m-%d')
        
        # Convert dates to timestamps
        start_ts = int(start_date.timestamp())
        end_ts = int(end_date.timestamp())

        # Reddit Comments Pipeline
        reddit_pipeline = [
            {
                '$match': {
                    'created_utc': {
                        '$gte': start_ts,
                        '$lte': end_ts
                    }
                }
            },
            {
                '$group': {
                    '_id': {
                        '$dateToString': {
                            'format': '%Y-%m-%d',
                            'date': {
                                '$toDate': {'$multiply': ['$created_utc', 1000]}
                            }
                        }
                    },
                    'count': {'$sum': 1}
                }
            },
            {'$sort': {'_id': 1}}
        ]
        
        # 4chan Posts Pipeline
        chan_pipeline = [
            {'$unwind': '$posts'},
            {
                '$match': {
                    'posts.time': {
                        '$gte': start_ts,
                        '$lte': end_ts
                    }
                }
            },
            {
                '$group': {
                    '_id': {
                        '$dateToString': {
                            'format': '%Y-%m-%d',
                            'date': {
                                '$toDate': {'$multiply': ['$posts.time', 1000]}
                            }
                        }
                    },
                    'count': {'$sum': 1}
                }
            },
            {'$sort': {'_id': 1}}
        ]
        
        reddit_results = list(db.reddit_comments.aggregate(reddit_pipeline))
        chan_results = list(db_chan['4chan_posts'].aggregate(chan_pipeline))
        
        # Convert to dataframes
        reddit_df = pd.DataFrame(reddit_results).rename(columns={'_id': 'date', 'count': 'Reddit Comments'})
        chan_df = pd.DataFrame(chan_results).rename(columns={'_id': 'date', 'count': '4chan Posts'})
        
        # Merge dataframes
        df = pd.merge(reddit_df, chan_df, on='date', how='outer').fillna(0)
        df = df.sort_values('date')
        
        # Create figure
        fig = go.Figure()
        
        # Add Reddit line
        fig.add_trace(go.Scatter(
            x=df['date'],
            y=df['Reddit Comments'],
            name='Reddit Comments',
            line=dict(color='#2ecc71', width=2),
            mode='lines+markers'
        ))
        
        # Add 4chan line
        fig.add_trace(go.Scatter(
            x=df['date'],
            y=df['4chan Posts'],
            name='4chan Posts',
            line=dict(color='#e74c3c', width=2),
            mode='lines+markers'
        ))
        
        # Update layout
        fig.update_layout(
            title='Platform Activity Comparison',
            xaxis_title='Date',
            yaxis_title='Number of Posts/Comments',
            hovermode='x unified',
            plot_bgcolor='white',
            paper_bgcolor='white',
            legend=dict(
                yanchor="top",
                y=0.99,
                xanchor="left",
                x=0.01
            )
        )
        
        # Add grid
        fig.update_xaxes(showgrid=True, gridwidth=1, gridcolor='lightgray')
        fig.update_yaxes(showgrid=True, gridwidth=1, gridcolor='lightgray')
        
        execution_time = time.time() - start_time
        
        return jsonify({
            'plot': json.loads(fig.to_json()),
            'execution_time': f'{execution_time:.2f}'
        })
        
    except Exception as e:
        app.logger.error(f'Error in volume comparison: {str(e)}')
        return jsonify({'error': str(e)}), 500

@app.route('/toxicity', methods=['POST'])
def toxicity():
    try:
        start_time = time.time()
        app.logger.info('Starting toxicity analysis')
        
        data = request.json
        start_date = datetime.strptime(data['start_date'], '%Y-%m-%d')
        end_date = datetime.strptime(data['end_date'], '%Y-%m-%d')
        threshold = float(data['threshold'])
        
        # Convert dates to timestamps
        start_ts = int(start_date.timestamp())
        end_ts = int(end_date.timestamp())
        
        pipeline = [
            {
                '$match': {
                    'created_utc': {'$gte': start_ts, '$lte': end_ts},
                    'toxicity_score': {'$ne': -1}  # Exclude NA values
                }
            },
            {
                '$addFields': {
                    'is_toxic': {
                        '$cond': [
                            {'$gte': ['$toxicity_score', threshold]},
                            'flag',
                            'normal'
                        ]
                    }
                }
            },
            {
                '$group': {
                    '_id': {
                        'date': {
                            '$dateToString': {
                                'format': '%Y-%m-%d',
                                'date': {
                                    '$toDate': {'$multiply': ['$created_utc', 1000]}
                                }
                            }
                        },
                        'class': '$is_toxic'
                    },
                    'count': {'$sum': 1},
                    'avg_score': {'$avg': '$toxicity_score'}
                }
            },
            {'$sort': {'_id.date': 1, '_id.class': 1}}
        ]
        
        results = list(db.reddit_comments.aggregate(pipeline))
        
        if not results:
            return jsonify({'error': 'No data found for the selected parameters'}), 404
        
        # Process results
        df = pd.DataFrame([
            {
                'date': r['_id']['date'],
                'class': r['_id']['class'],
                'count': r['count'],
                'avg_score': r['avg_score']
            } for r in results
        ])
        
        # Create figure
        fig = go.Figure()
        
        colors = {'normal': '#2ecc71', 'flag': '#e74c3c'}
        
        for toxicity_class in ['normal', 'flag']:
            mask = df['class'] == toxicity_class
            if mask.any():
                fig.add_trace(go.Bar(
                    x=df[mask]['date'],
                    y=df[mask]['count'],
                    name=f'{toxicity_class.title()}',
                    marker_color=colors[toxicity_class],
                    text=df[mask]['avg_score'].round(3),
                    textposition='auto',
                    hovertemplate="Date: %{x}<br>" +
                                "Count: %{y}<br>" +
                                "Avg Score: %{text}<br>" +
                                "<extra></extra>"
                ))
        
        # Update layout
        fig.update_layout(
            title=f'Daily Comment Distribution by Toxicity (Threshold: {threshold})',
            xaxis_title='Date',
            yaxis_title='Number of Comments',
            barmode='stack',
            hovermode='x unified',
            showlegend=True,
            plot_bgcolor='white',
            paper_bgcolor='white'
        )
        
        # Add grid
        fig.update_xaxes(showgrid=True, gridwidth=1, gridcolor='lightgray')
        fig.update_yaxes(showgrid=True, gridwidth=1, gridcolor='lightgray')
        
        execution_time = time.time() - start_time
        
        return jsonify({
            'plot': json.loads(fig.to_json()),
            'execution_time': f'{execution_time:.2f}'
        })
        
    except Exception as e:
        app.logger.error(f'Error in toxicity analysis: {str(e)}')
        return jsonify({'error': str(e)}), 500

@app.route('/word_search', methods=['POST'])
def word_search():
    try:
        start_time = time.time()
        app.logger.info('Starting word search analysis')
        
        data = request.json
        word = data['word'].strip().lower()
        platform = data['platform']
        
        if not word:
            return jsonify({'error': 'Search word cannot be empty'}), 400
            
        app.logger.info(f'Parameters - Word: {word}, Platform: {platform}')
        
        # Fixed date range Nov 1-14
        start_ts = datetime(2024, 11, 1).timestamp()
        end_ts = datetime(2024, 11, 14, 23, 59, 59).timestamp()

        if platform == 'reddit_comments':
            pipeline = [
                {
                    '$match': {
                        'created_utc': {'$gte': start_ts, '$lte': end_ts},
                        'body': {'$regex': word, '$options': 'i'}
                    }
                },
                {
                    '$group': {
                        '_id': {
                            '$dateToString': {
                                'format': '%Y-%m-%d',
                                'date': {
                                    '$toDate': {'$multiply': ['$created_utc', 1000]}
                                }
                            }
                        },
                        'count': {'$sum': 1}
                    }
                },
                {'$sort': {'_id': 1}}
            ]
            collection = db.reddit_comments
        else:  # 4chan posts
            pipeline = [
                {'$unwind': '$posts'},
                {
                    '$match': {
                        'posts.time': {'$gte': start_ts, '$lte': end_ts},
                        'posts.com': {'$regex': word, '$options': 'i'}
                    }
                },
                {
                    '$group': {
                        '_id': {
                            '$dateToString': {
                                'format': '%Y-%m-%d',
                                'date': {
                                    '$toDate': {'$multiply': ['$posts.time', 1000]}
                                }
                            }
                        },
                        'count': {'$sum': 1}
                    }
                },
                {'$sort': {'_id': 1}}
            ]
            collection = db_chan['4chan_posts']
        
        results = list(collection.aggregate(pipeline))
        
        if not results:
            app.logger.warning(f'No occurrences found for word: {word}')
            return jsonify({'error': f'No occurrences found for "{word}"'}), 404
        
        dates = [r['_id'] for r in results]
        counts = [r['count'] for r in results]
        
        fig = px.bar(x=dates, y=counts,
                    title=f'Occurrences of "{word}" in {platform}',
                    labels={'x': 'Date', 'y': 'Count'})
        
        execution_time = time.time() - start_time
        app.logger.info(f'Word search completed in {execution_time:.2f} seconds')
        
        return jsonify({
            'plot': json.loads(fig.to_json()),
            'execution_time': f'{execution_time:.2f}'
        })
        
    except Exception as e:
        app.logger.error(f'Error in word search: {str(e)}')
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)