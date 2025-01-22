from pymongo import MongoClient
from datetime import datetime, timedelta
from pprint import pprint

def verify_4chan_toxicity():
    try:
        # Connect to MongoDB
        client = MongoClient("mongodb://localhost:27017/")
        db = client["chan_crawler"]
        posts_collection = db["4chan_posts"]

        print("\n=== Checking Recent 4chan Posts (Last 15 minutes) ===")

        # Get timestamp for 15 minutes ago
        fifteen_mins_ago = datetime.utcnow() - timedelta(minutes=15)

        # Query recent posts
        recent_posts = posts_collection.find(
            {
                'collected_at': {'$gte': fifteen_mins_ago}
            },
            {
                '_id': 1,
                'posts': 1,
                'board': 1,
                'collected_at': 1
            }
        ).limit(5)

        post_count = 0
        with_toxicity = 0

        for thread in recent_posts:
            print(f"\nThread ID: {thread.get('_id')}")
            print(f"Board: {thread.get('board', 'N/A')}")
            print(f"Collected at: {thread.get('collected_at', 'N/A')}")
            
            for post in thread.get('posts', []):
                post_count += 1
                print(f"\nPost Number: {post.get('no')}")
                print(f"Time: {datetime.fromtimestamp(post.get('time'))}")
                if post.get('com'):
                    print(f"Content preview: {post.get('com')[:100]}...")
                
                if 'toxicity_score' in post and 'toxicity_class' in post:
                    with_toxicity += 1
                    print(f"Toxicity Class: {post.get('toxicity_class')}")
                    print(f"Toxicity Score: {post.get('toxicity_score')}")
                    print(f"Processed At: {post.get('toxicity_processed_at')}")
                else:
                    print("Toxicity Scoring: NOT PRESENT")
                print("-" * 80)

        print("\n=== Summary ===")
        print(f"Posts checked: {post_count}")
        print(f"Posts with toxicity scores: {with_toxicity}")

        # Get statistics for the last hour
        one_hour_ago = datetime.utcnow() - timedelta(hours=1)
        total_last_hour = posts_collection.count_documents({
            'collected_at': {'$gte': one_hour_ago}
        })

        with_toxicity_last_hour = posts_collection.count_documents({
            'collected_at': {'$gte': one_hour_ago},
            'posts.toxicity_score': {'$exists': True}
        })

        print("\n=== Last Hour Statistics ===")
        print(f"Total threads collected: {total_last_hour}")
        print(f"Threads with toxicity scores: {with_toxicity_last_hour}")
        if total_last_hour > 0:
            coverage_percentage = (with_toxicity_last_hour / total_last_hour) * 100
            print(f"Coverage percentage: {coverage_percentage:.2f}%")

    except Exception as e:
        print(f"Error running verification: {str(e)}")

if __name__ == "__main__":
    verify_4chan_toxicity()
