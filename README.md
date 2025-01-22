# Political Discourse Analysis Platform: 2024 U.S. Presidential Election

## Short Description
A comprehensive social media analysis platform analyzing political discourse during the 2024 U.S. Presidential Election by collecting and processing over 4.6 million 4chan posts and 1.2 million Reddit comments. Features real-time sentiment analysis, toxicity tracking, and interactive visualizations through a web dashboard.

## Project Overview
This project evolved through three phases:
1. Data Collection Pipeline Development
2. Data Analysis and Visualization Implementation
3. Interactive Dashboard Creation

### Data Collection Statistics (Nov 1 - Dec 12, 2024)
- **4chan Posts:** 4.6 million
- **Reddit Comments:** 1.2 million
- **Reddit Posts:** 20,000
- **Peak Traffic:** Election Day (Nov 6) with ~250,000 4chan posts and ~145,000 Reddit comments
- **Toxicity Analysis:** Only 3% of Reddit comments flagged as toxic

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
├── Project_Report.pdf
└── README.md
```

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
     
## Technical Implementation

### Data Collection Infrastructure
- **Job Scheduling:** Faktory for distributed task management
- **Database:** MongoDB for flexible schema and high write throughput
- **Rate Limiting:** Intelligent backoff strategies for API limits
- **Error Recovery:** Automatic retry mechanism for failed requests

### Performance Optimizations
1. **Memory Management:**
   - Implemented multi-threading for parallel processing
   - Batch processing for large data volumes
   - Memory-efficient data streaming

2. **High Traffic Handling:**
   - Queue-based job scheduling during peak periods
   - Backlog management during Election Day surge
   - Automatic recovery from API rate limits

3. **Data Processing:**
   - Pre-processed CSV exports for visualization efficiency
   - Parallel data processing for toxicity analysis
   - Optimized MongoDB queries with proper indexing

### Real-time Analysis Features
- **Sentiment Analysis:** Tracking discussion tone evolution
- **Toxicity Monitoring:** ModerateHatespeech API integration
- **Volume Analysis:** Cross-platform activity comparison
- **Word Frequency:** Dynamic topic tracking

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

## Key Features
1. **Volume Analysis Comparison**
   - Cross-platform activity tracking
   - Interactive date range selection
   - Real-time visualization

2. **Toxicity Analysis**
   - Comment toxicity distribution
   - Adjustable thresholds
   - Platform comparison metrics

3. **Word Frequency Analysis**
   - Topic evolution tracking
   - Platform-specific trends
   - Election event impact analysis

## Technical Challenges & Solutions
1. **VM Memory Constraints**
   - Implemented parallel processing
   - Optimized data batch sizes
   - Added memory-efficient streaming

2. **API Rate Limits**
   - Intelligent retry mechanisms
   - Queue-based job scheduling
   - Distributed request handling

3. **Peak Traffic Management**
   - Elastic job queuing
   - Prioritized processing
   - Automated recovery systems

## License
This project is part of CS 415/515 at Binghamton University. All rights reserved.
