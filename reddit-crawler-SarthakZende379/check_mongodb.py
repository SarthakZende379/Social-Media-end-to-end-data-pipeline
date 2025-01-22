# from pymongo import MongoClient
# client = MongoClient('mongodb://localhost:27017/')
# db = client.reddit_crawler

# # Check recent posts
# recent_posts = list(db.reddit_posts.find().sort('collected_at', -1).limit(1))
# print(f"Recent posts count: {db.reddit_posts.count_documents({})}")
# if recent_posts:
#     print(f"Most recent post: {recent_posts[0].get('subreddit')} - {recent_posts[0].get('title')}")

# from pymongo import MongoClient
# client = MongoClient()
# db = client.reddit_crawler
# print(f"Posts count: {db.reddit_posts.count_documents({'subreddit': 'politics'})}")

# check_collection_timing.py-------Working previously
# from pymongo import MongoClient
# from datetime import datetime, timezone, timedelta
# import pandas as pd

# def analyze_reddit_collection():
#     client = MongoClient('mongodb://localhost:27017/')
#     db = client.reddit_crawler
#     collection = db.reddit_posts
    
#     # Reference time: November 17, 2024
#     reference_time = datetime(2024, 11, 17, tzinfo=timezone.utc)
    
#     # Get all posts with timestamps
#     cursor = collection.find(
#         {'subreddit': 'politics'},
#         {'created_utc': 1, 'title': 1}
#     )
    
#     # Convert to DataFrame for easier analysis
#     posts_df = pd.DataFrame(list(cursor))
    
#     if len(posts_df) == 0:
#         print("No posts found in collection!")
#         return
        
#     # Convert timestamps to datetime with UTC timezone
#     posts_df['datetime'] = pd.to_datetime(posts_df['created_utc'], unit='s', utc=True)
    
#     # Sort by timestamp
#     posts_df = posts_df.sort_values('datetime')
    
#     print("\nCollection Analysis:")
#     print(f"Total posts: {len(posts_df)}")
#     print(f"\nTimestamp Range:")
#     print(f"Earliest post: {posts_df['datetime'].min()}")
#     print(f"Latest post: {posts_df['datetime'].max()}")
#     print(f"Reference time (Now): {reference_time}")
    
#     # Get distribution of posts by day for the last 5 days
#     latest_post_time = posts_df['datetime'].max()
#     five_days_ago = latest_post_time - timedelta(days=5)
#     recent_posts = posts_df[posts_df['datetime'] > five_days_ago]
    
#     print("\nPosts per day (last 5 days):")
#     daily_counts = recent_posts.set_index('datetime').resample('D').size()
#     for day, count in daily_counts.items():
#         print(f"{day.date()}: {count} posts")
    
#     print("\nLatest 5 posts:")
#     latest_posts = posts_df.nlargest(5, 'datetime')[['datetime', 'title']]
#     for _, post in latest_posts.iterrows():
#         print(f"\n{post['datetime']}: {post['title']}")

# if __name__ == "__main__":
#     analyze_reddit_collection()

#-----------------------------------------------------------------------
from pymongo import MongoClient
from datetime import datetime, timedelta
import json
from pprint import pprint

def verify_toxicity_scoring():
    # Load config
    with open('config.json', 'r') as f:
        config = json.load(f)

    # Connect to MongoDB
    client = MongoClient(config['mongodb']['uri'])
    db = client[config['mongodb']['database']]
    comments_collection = db[config['mongodb']['collections']['comments']]

    # Get timestamp for 15 minutes ago
    fifteen_mins_ago = datetime.utcnow() - timedelta(minutes=15)

    # Query recent comments
    recent_comments = comments_collection.find(
        {
            'collected_at': {'$gte': fifteen_mins_ago}
        },
        {
            '_id': 1,
            'body': 1,
            'toxicity_class': 1,
            'toxicity_score': 1,
            'collected_at': 1,
            'subreddit': 1
        }
    ).sort('collected_at', -1).limit(5)

    print("\n=== Checking Recent Comments (Last 15 minutes) ===")
    comment_count = 0
    with_toxicity = 0
    
    for comment in recent_comments:
        comment_count += 1
        print("\nComment ID:", comment['_id'])
        print("Subreddit:", comment.get('subreddit', 'N/A'))
        print("Collected at:", comment.get('collected_at', 'N/A'))
        print("Body preview:", comment.get('body', 'N/A')[:100] + '...' if comment.get('body') else 'N/A')
        
        if 'toxicity_score' in comment and 'toxicity_class' in comment:
            with_toxicity += 1
            print("Toxicity Class:", comment.get('toxicity_class'))
            print("Toxicity Score:", comment.get('toxicity_score'))
        else:
            print("Toxicity Scoring: NOT PRESENT")
        print("-" * 80)

    print("\n=== Summary ===")
    print(f"Comments checked: {comment_count}")
    print(f"Comments with toxicity scores: {with_toxicity}")
    
    # Get statistics for the last hour
    one_hour_ago = datetime.utcnow() - timedelta(hours=1)
    
    total_last_hour = comments_collection.count_documents({
        'collected_at': {'$gte': one_hour_ago}
    })
    
    with_toxicity_last_hour = comments_collection.count_documents({
        'collected_at': {'$gte': one_hour_ago},
        'toxicity_score': {'$exists': True}
    })

    print("\n=== Last Hour Statistics ===")
    print(f"Total comments collected: {total_last_hour}")
    print(f"Comments with toxicity scores: {with_toxicity_last_hour}")
    if total_last_hour > 0:
        coverage_percentage = (with_toxicity_last_hour / total_last_hour) * 100
        print(f"Coverage percentage: {coverage_percentage:.2f}%")

if __name__ == "__main__":
    try:
        verify_toxicity_scoring()
    except Exception as e:
        print(f"Error running verification: {str(e)}")