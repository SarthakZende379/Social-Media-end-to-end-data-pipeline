# 4chan_plots.py
import matplotlib.pyplot as plt
from pymongo import MongoClient
from datetime import datetime, timedelta
import pandas as pd

MONGO_URI = "mongodb://localhost:27017/"
DB_NAME = "chan_crawler"
COLLECTION_NAME = "4chan_posts"

def generate_4chan_plots():
    client = MongoClient(MONGO_URI)
    db = client[DB_NAME]
    
    # Define the date range we want to analyze
    start_timestamp = 1698796800  # Nov 1, 2024 00:00:00 UTC
    end_timestamp = 1699228799   # Nov 5, 2024 23:59:59 UTC
    
    # Modified pipeline for Nov 1-5
    pipeline = [
        {
            "$unwind": "$posts"
        },
        {
            "$addFields": {
                "date": {
                    "$dateToString": {
                        "format": "%Y-%m-%d",
                        "date": {
                            "$toDate": {
                                "$multiply": ["$posts.time", 1000]
                            }
                        }
                    }
                }
            }
        },
        {
            "$match": {
                "date": {
                    "$in": [
                        "2024-11-01",
                        "2024-11-02",
                        "2024-11-03",
                        "2024-11-04",
                        "2024-11-05"
                    ]
                }
            }
        },
        {
            "$group": {
                "_id": "$date",
                "count": {"$sum": 1}
            }
        },
        {
            "$sort": {"_id": 1}
        }
    ]
    
    data = list(db[COLLECTION_NAME].aggregate(pipeline))
    
    if not data:
        print("No data found for Nov 1-5, 2024!")
        return {
            "total_posts": 0,
            "days_collected": 0,
            "avg_posts_per_day": 0,
            "collection_period": "No data"
        }

    # Print data for Nov 1-5
    print("\n=== 4chan Posts Collected (Nov 1-5, 2024) ===")
    print("Date            Posts")
    print("--------------------")
    total_posts = 0
    dates = []
    counts = []
    
    # Initialize all dates
    date_data = {
        "2024-11-01": 0,
        "2024-11-02": 0,
        "2024-11-03": 0,
        "2024-11-04": 0,
        "2024-11-05": 0
    }
    
    # Fill in actual data
    for d in data:
        date_data[d["_id"]] = d["count"]
    
    # Print all dates, even if no data
    for date, count in date_data.items():
        print(f"{date}:  {count:,} posts")
        total_posts += count
        dates.append(date)
        counts.append(count)
    
    print("\n=== Summary Statistics ===")
    print(f"Total Posts: {total_posts:,}")
    print(f"Average Posts per Day: {total_posts/5:,.2f}")
    
    # Create plot
    plt.figure(figsize=(12, 6))
    plt.plot(dates, counts, marker='o', linewidth=2)
    plt.title('4chan Posts Collected (Nov 1-5, 2024)')
    plt.xlabel('Date')
    plt.ylabel('Number of Posts')
    plt.grid(True, linestyle='--', alpha=0.7)
    plt.xticks(rotation=45)
    plt.tight_layout()
    plt.savefig('4chan_daily_collection.png')
    plt.close()
    
    # Save stats to a file
    with open('4chan_collection_stats.txt', 'w') as f:
        f.write("4chan Data Collection Statistics (Nov 1-5, 2024):\n")
        f.write("==========================================\n")
        f.write("\nDaily Breakdown:\n")
        for date, count in date_data.items():
            f.write(f"{date}: {count:,} posts\n")
        f.write("\nSummary:\n")
        f.write(f"Total Posts: {total_posts:,}\n")
        f.write(f"Average Posts per Day: {total_posts/5:,.2f}\n")

    return {
        "total_posts": total_posts,
        "days_collected": 5,
        "avg_posts_per_day": total_posts/5,
        "collection_period": "2024-11-01 to 2024-11-05"
    }

if __name__ == "__main__":
    try:
        client = MongoClient(MONGO_URI)
        db = client[DB_NAME]
        
        print("Running 4chan data analysis for Nov 1-5, 2024...")
        stats = generate_4chan_plots()
        
        print("\nAnalysis complete! Check '4chan_collection_stats.txt' for full details")
        print("and '4chan_daily_collection.png' for the visualization.")
            
    except Exception as e:
        print(f"Error: {e}")