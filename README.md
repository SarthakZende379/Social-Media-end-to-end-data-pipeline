# Political Discourse Analysis Platform: 2024 U.S. Presidential Election

## Short Description
A comprehensive social media analysis platform analyzing political discourse during the 2024 U.S. Presidential Election by collecting and processing over 4.6 million 4chan posts and 1.2 million Reddit comments. Features real-time sentiment analysis, toxicity tracking, and interactive visualizations through a web dashboard.

## Project Overview
This project evolved through three phases:
1. Data Collection Pipeline Development
2. Data Analysis and Visualization Implementation
3. Interactive Dashboard Creation

### Current Statistics (Nov 1 - Dec 12, 2024)
- **4chan Posts:** 4.6 million
- **Reddit Comments:** 1.2 million
- **Reddit Posts:** 20,000
- **Peak Traffic:** Election Day (Nov 6) with ~250,000 4chan posts and ~145,000 Reddit comments
- **Toxicity Analysis:** Only 3% of Reddit comments flagged as toxic

## Project Structure
```
.
├── 4chan-crawler-SarthakZende379/    # 4chan data collection module
│   ├── chan_client.py               # API client implementation
│   ├── chan_crawler.py              # Main crawler
│   ├── cold_start_board.py          # Crawler initialization
│   └── ...
├── reddit-crawler-SarthakZende379/   # Reddit data collection module
│   ├── reddit_client.py             # API client
│   ├── reddit_crawler.py            # Main crawler
│   ├── historical_toxicity.py       # Toxicity processor
│   └── ...
└── website/                         # Analysis dashboard
    ├── app.py                       # Flask application
    └── templates/                   # Frontend views
```

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

### 1. Environment Setup
1. Clone the repository:
   ```bash
   git clone [repository-url]
   cd [repository-name]
   ```

2. Install dependencies:
   ```bash
   pip install -r website/requirements.txt
   ```

### 2. Service Configuration
1. Start required services:
   ```bash
   docker start mongodb
   docker start faktory
   ```

2. Port Forwarding (if remote):
   ```bash
   ssh -L 27017:localhost:27017 username@<VM_IP>  # MongoDB
   ssh -L 7420:localhost:7420 username@<VM_IP>    # Faktory Dashboard
   ssh -L 5000:localhost:5000 username@<VM_IP>    # Web Dashboard
   ```

### 3. Data Collection
1. Start 4chan Crawler:
   ```bash
   cd 4chan-crawler-SarthakZende379
   python cold_start_board.py pol
   python chan_crawler.py
   ```

2. Start Reddit Crawler:
   ```bash
   cd reddit-crawler-SarthakZende379
   python cold_start_subreddit.py
   python reddit_crawler.py
   ```

### 4. Dashboard Access
- MongoDB Compass: `mongodb://localhost:27017`
- Faktory Dashboard: http://localhost:7420
- Analysis Dashboard: http://localhost:5000

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
