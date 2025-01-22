from pymongo import MongoClient
from datetime import datetime

def count_posts():
    # MongoDB connection settings
    MONGO_URI = "mongodb://localhost:27017/"
    DB_NAME = "chan_crawler"
    COLLECTION_NAME = "4chan_posts"
    
    try:
        # Connect to MongoDB
        client = MongoClient(MONGO_URI)
        db = client[DB_NAME]
        
        # Pipeline to count total posts
        pipeline = [
            {
                "$unwind": "$posts"  # Unwind the posts array
            },
            {
                "$group": {
                    "_id": None,
                    "total_posts": {"$sum": 1},
                    "first_post_time": {"$min": "$posts.time"},
                    "last_post_time": {"$max": "$posts.time"}
                }
            }
        ]
        
        result = list(db[COLLECTION_NAME].aggregate(pipeline))
        
        if not result:
            print("No posts found in the database!")
            return
            
        stats = result[0]
        
        # Convert timestamps to readable dates
        first_date = datetime.fromtimestamp(stats["first_post_time"]).strftime('%Y-%m-%d %H:%M:%S')
        last_date = datetime.fromtimestamp(stats["last_post_time"]).strftime('%Y-%m-%d %H:%M:%S')
        
        # Calculate time span in days
        days_span = (stats["last_post_time"] - stats["first_post_time"]) / 86400  # 86400 seconds in a day
        
        # Print results
        print("\n4chan Data Collection Statistics:")
        print("==============================")
        print(f"Total posts collected: {stats['total_posts']:,}")
        print(f"\nCollection period:")
        print(f"Start date: {first_date}")
        print(f"End date: {last_date}")
        print(f"Time span: {days_span:.2f} days")
        print(f"Average posts per day: {stats['total_posts']/days_span:,.2f}")
        
        return stats
        
    except Exception as e:
        print(f"Error: {e}")
        return None
    finally:
        client.close()

if __name__ == "__main__":
    count_posts()