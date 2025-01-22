# Social Media Analysis Dashboard - Project 3

This project implements an interactive web dashboard for analyzing social media data collected from Reddit and 4chan during the 2024 U.S. Presidential Election period. The dashboard provides visualizations for volume analysis, toxicity trends, and word frequency patterns.

## Project Structure

```
.
├── 4chan-crawler-SarthakZende379/    # 4chan data collection module
│   ├── chan_client.py               # 4chan API client implementation
│   ├── chan_crawler.py              # Main crawler implementation
│   ├── cold_start_board.py          # Initialize crawler for new board
│   ├── 4chan_plots.py               # Data visualization scripts
│   └── requirements.txt             # Python dependencies
│
├── reddit-crawler-SarthakZende379/   # Reddit data collection module
│   ├── reddit_client.py             # Reddit API client implementation
│   ├── reddit_crawler.py            # Main crawler implementation
│   ├── cold_start_subreddit.py      # Initialize crawler for subreddits
│   ├── reddit_plots.py              # Data visualization scripts
│   ├── historical_toxicity.py       # Toxicity analysis processor
│   ├── config.json                  # Configuration settings
│   └── requirements.txt             # Python dependencies
│
├── website/                          # Web dashboard implementation
│   ├── app.py                       # Flask application
│   ├── requirements.txt             # Python dependencies
│   ├── static/                      # Static assets
│   ├── templates/                   # HTML templates
│   │   └── index.html              # Dashboard template
│   └── logs/                        # Application logs
│
├── HONESTY.md
├── CREDITS.md
└── README.md
```

## Data Collection Statistics (Nov 1 - Dec 12, 2024 10:15 AM)
- **4chan Posts:** 4.6 million posts
- **Reddit Comments:** 1.2 million comments
- **Reddit Posts:** 20,000 posts

## Key Analysis Insights
1. **Activity Patterns**
   - Significant activity spike across platforms on Election Day (Nov 6)
   - 4chan shows more volatile daily fluctuations (~250,000 peak posts)
   - Reddit demonstrates more stable engagement patterns

2. **Content Analysis**
   - Only 3% of Reddit comments flagged as toxic (threshold ≥ 0.7)
   - Higher comment volumes during election events maintained similar toxicity ratios
   - Platform-specific topic trends visible through word frequency analysis

3. **Research Focus**
   - Comparative platform behavior during political events
   - Moderation effectiveness analysis
   - Evolution of discussion themes over time

## Setup Instructions

### 1. Start Required Services

1. Start MongoDB:
   ```bash
   docker start mongodb
   ```

2. Start Faktory:
   ```bash
   docker start faktory
   ```

3. Verify services are running:
   ```bash
   docker ps
   ```

### 2. Set Up Port Forwarding (if accessing remotely)

1. MongoDB port forwarding:
   ```bash
   ssh -L 27017:localhost:27017 username@<VM_IP_ADDRESS>
   ```

2. Faktory Dashboard port forwarding:
   ```bash
   ssh -L 7420:localhost:7420 username@<VM_IP_ADDRESS>
   ```
   Access Faktory dashboard at: http://localhost:7420

3. Website port forwarding:
   ```bash
   ssh -L 5000:localhost:5000 username@<VM_IP_ADDRESS>
   ```

### 3. Data Collection Setup

1. Start 4chan Crawler:
   ```bash
   cd 4chan-crawler-SarthakZende379
   source ../env/bin/activate
   python cold_start_board.py pol    # Initialize crawler
   python chan_crawler.py            # Run continuous crawler
   ```

2. Start Reddit Crawler:
   ```bash
   cd reddit-crawler-SarthakZende379
   source ../env/bin/activate
   python cold_start_subreddit.py    # Initialize crawler
   python reddit_crawler.py          # Run continuous crawler
   ```

### 4. Run the Dashboard

1. Install required dependencies:
   ```bash
   cd website
   pip install -r requirements.txt
   ```

2. Start the Flask application:
   ```bash
   python app.py
   ```

3. Access the dashboard at http://localhost:5000

## Data Requirements

- MongoDB database with collections:
  - reddit_crawler.reddit_comments
  - chan_crawler.4chan_posts
- Date range: November 1-14, 2024
- Toxicity scores for Reddit comments (Nov 1-7)

## Implementation Notes

- Backend: Flask, MongoDB
- Frontend: Bootstrap, Plotly.js
- Real-time data processing
- Interactive visualizations
- Error handling and loading states

## Accessing Tools

1. MongoDB Compass:
   - Connect using: `mongodb://localhost:27017`

2. Faktory Dashboard:
   - Access at: http://localhost:7420

3. Analysis Dashboard:
   - Access at: http://localhost:5000

## Team

Binary Bandits - CS-515
