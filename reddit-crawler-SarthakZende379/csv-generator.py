from pymongo import MongoClient
from datetime import datetime, timezone
import pandas as pd
import logging

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def generate_politics_comments_per_hour():
    """
    Generate CSV file with hourly comment counts for r/politics
    Format: hour (ISO 8601), num_comments
    Period: Nov 1-14, 2024
    """
    
    # MongoDB connection settings
    MONGO_URI = "mongodb://localhost:27017/"
    DB_NAME = "reddit_crawler"
    COLLECTION = "reddit_comments"
    
    try:
        # Connect to MongoDB
        client = MongoClient(MONGO_URI)
        db = client[DB_NAME]
        collection = db[COLLECTION]
        
        # Define time range (Nov 1-14, 2024 UTC)
        start_time = int(datetime(2024, 11, 1).replace(tzinfo=timezone.utc).timestamp())
        end_time = int(datetime(2024, 11, 15).replace(tzinfo=timezone.utc).timestamp())  # Include full day of 14th
        
        # Aggregate pipeline to get hourly counts
        pipeline = [
            # Match politics comments in date range
            {"$match": {
                "subreddit": "politics",
                "created_utc": {"$gte": start_time, "$lt": end_time}
            }},
            # Group by hour
            {"$group": {
                "_id": {
                    "$dateToString": {
                        "format": "%Y-%m-%dT%H:00:00Z",
                        "date": {
                            "$toDate": {
                                "$multiply": ["$created_utc", 1000]
                            }
                        }
                    }
                },
                "num_comments": {"$sum": 1}
            }},
            # Sort by hour
            {"$sort": {"_id": 1}}
        ]
        
        logger.info("Executing MongoDB aggregation...")
        results = list(collection.aggregate(pipeline))
        
        # Convert to DataFrame
        df = pd.DataFrame(results)
        df.columns = ['hour', 'num_comments']
        
        # Ensure we have all hours (even those with 0 comments)
        date_range = pd.date_range(
            start=datetime(2024, 11, 1, tzinfo=timezone.utc),
            end=datetime(2024, 11, 14, 23, tzinfo=timezone.utc),
            freq='H'
        )
        
        # Create complete DataFrame with all hours
        full_df = pd.DataFrame({'hour': date_range.strftime('%Y-%m-%dT%H:00:00Z')})
        full_df = full_df.merge(df, on='hour', how='left')
        full_df['num_comments'] = full_df['num_comments'].fillna(0).astype(int)
        
        # Save to CSV
        output_file = 'r-politics-comments-per-hour.csv'
        full_df.to_csv(output_file, index=False)
        logger.info(f"CSV file generated: {output_file}")
        
        # Print summary statistics
        total_comments = full_df['num_comments'].sum()
        logger.info(f"Total comments processed: {total_comments:,}")
        logger.info(f"Time period: {full_df['hour'].iloc[0]} to {full_df['hour'].iloc[-1]}")
        
    except Exception as e:
        logger.error(f"Error generating CSV: {e}")
        raise
    finally:
        client.close()

if __name__ == "__main__":
    generate_politics_comments_per_hour()