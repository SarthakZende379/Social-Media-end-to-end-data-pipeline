import pymongo
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from datetime import datetime
import logging

# Setup logging
logging.basicConfig(
    level=logging.INFO, 
    format='%(asctime)s - %(levelname)s - %(message)s'
)

# Setup plot styles using Seaborn
sns.set(style='darkgrid')  # Apply Seaborn's 'darkgrid' style
# Remove or comment out the Matplotlib style line
# plt.style.use('seaborn')  # This line is not needed and causes an error

def fetch_politics_hourly_comments(start_date, end_date):
    """Fetch hourly comments from r/politics within the date range."""
    try:
        client = pymongo.MongoClient("mongodb://localhost:27017/")
        comments_collection = client['reddit_crawler']['reddit_comments']

        # Convert dates to timestamps
        start_ts = pd.Timestamp(start_date).timestamp()
        end_ts = pd.Timestamp(end_date).timestamp()

        # Define aggregation pipeline
        pipeline = [
            {'$match': {'subreddit': 'politics'}},
            {'$unwind': '$comments_data'},
            {
                '$match': {
                    'comments_data.created_utc': {'$gte': start_ts, '$lte': end_ts}
                }
            },
            {
                '$project': {
                    'created_utc': '$comments_data.created_utc'
                }
            },
            {
                '$group': {
                    '_id': {
                        'datetime': {
                            '$dateToString': {
                                'format': '%Y-%m-%d %H:00:00',
                                'date': {
                                    '$toDate': {
                                        '$multiply': ['$created_utc', 1000]
                                    }
                                }
                            }
                        }
                    },
                    'count': {'$sum': 1}
                }
            },
            {'$sort': {'_id.datetime': 1}}
        ]

        # Execute aggregation
        logging.info("Fetching data from MongoDB...")
        results = list(comments_collection.aggregate(pipeline))
        logging.info(f"Fetched {len(results)} hourly comment records.")
        return results

    except Exception as e:
        logging.error(f"Error fetching data: {e}")
        return []

def plot_hourly_comments(data, output_path):
    """Plot hourly comments on r/politics."""
    if not data:
        logging.error("No data to plot.")
        return

    # Convert to DataFrame
    df = pd.DataFrame(data)

    # Ensure '_id' and 'count' are in DataFrame
    if '_id' not in df.columns or 'count' not in df.columns:
        logging.error("Data format is incorrect. Missing '_id' or 'count' in DataFrame.")
        logging.debug(f"DataFrame columns: {df.columns}")
        return

    # Extract datetime and count
    df['datetime'] = pd.to_datetime(df['_id'].apply(lambda x: x['datetime']))
    df['count'] = df['count']

    # Sort by datetime
    df = df.sort_values('datetime')

    # Plotting
    plt.figure(figsize=(15, 6))
    plt.plot(df['datetime'], df['count'], marker='.', linewidth=1, color='#2ecc71')
    plt.title('Hourly Comments on r/politics (Nov 1-14, 2024)')
    plt.xlabel('Date and Hour')
    plt.ylabel('Number of Comments')
    plt.xticks(rotation=45)
    plt.tight_layout()
    plt.savefig(output_path, dpi=300)
    plt.close()
    logging.info(f"Saved plot to {output_path}")

def main():
    # Define date range
    start_date = "2024-11-01"
    end_date = "2024-11-14"

    # Fetch data
    data = fetch_politics_hourly_comments(start_date, end_date)

    # Plot data
    output_path = 'politics_hourly_comments.png'
    plot_hourly_comments(data, output_path)

if __name__ == "__main__":
    main()
