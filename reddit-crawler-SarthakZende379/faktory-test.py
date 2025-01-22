# faktory-test.py for Reddit crawler

import logging
from pyfaktory import Client, Consumer, Job, Producer
import time
import random
from datetime import datetime

# Logger setup
logger = logging.getLogger("faktory test")
logger.propagate = False
logger.setLevel(logging.INFO)
sh = logging.StreamHandler()
formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
sh.setFormatter(formatter)
logger.addHandler(sh)

def test_subreddit_crawl(subreddit):
    """Simulate crawling a subreddit"""
    logger.info(f"Starting test crawl for r/{subreddit}")
    sleep_for = random.randint(1, 5)
    time.sleep(sleep_for)
    logger.info(f"Finished crawling r/{subreddit} after {sleep_for} seconds")
    return {"subreddit": subreddit, "posts": random.randint(10, 100)}

def test_comment_crawl(post_id, subreddit):
    """Simulate crawling comments"""
    logger.info(f"Starting test comment crawl for post {post_id} in r/{subreddit}")
    sleep_for = random.randint(1, 3)
    time.sleep(sleep_for)
    logger.info(f"Finished crawling comments after {sleep_for} seconds")
    return {"post_id": post_id, "comments": random.randint(5, 50)}

def produce_test_jobs(faktory_server_url):
    try:
        with Client(faktory_url=faktory_server_url, role="producer") as client:
            producer = Producer(client=client)
            
            # Read subreddits from config
            test_subreddits = ["politics", "conservative", "democrat", "republican"]
            
            # Generate subreddit crawl jobs
            subreddit_jobs = []
            for subreddit in test_subreddits:
                job = Job(
                    jobtype="reddit-subreddit-crawl",
                    args=(subreddit,),
                    queue="reddit-crawl"
                )
                subreddit_jobs.append(job)
            
            producer.push_bulk(subreddit_jobs)
            logger.info(f"Enqueued {len(subreddit_jobs)} subreddit crawl jobs")
            
            # Generate comment crawl jobs
            comment_jobs = []
            for i in range(5):
                job = Job(
                    jobtype="reddit-comment-crawl",
                    args=(f"post_id_{i}", "politics"),
                    queue="reddit-crawl"
                )
                comment_jobs.append(job)
            
            producer.push_bulk(comment_jobs)
            logger.info(f"Enqueued {len(comment_jobs)} comment crawl jobs")
            
    except Exception as e:
        logger.error(f"Error producing test jobs: {e}")

def start_test_consumer(faktory_server_url):
    try:
        with Client(faktory_url=faktory_server_url, role="consumer") as client:
            consumer = Consumer(
                client=client,
                queues=["reddit-crawl"],
                concurrency=3
            )
            
            # Register test handlers
            consumer.register("reddit-subreddit-crawl", test_subreddit_crawl)
            consumer.register("reddit-comment-crawl", test_comment_crawl)
            
            logger.info("Starting test consumer")
            consumer.run()
            
    except Exception as e:
        logger.error(f"Error starting test consumer: {e}")

def test_rate_limiting():
    """Test rate limiting functionality"""
    start_time = datetime.now()
    requests = 0
    
    for i in range(5):
        logger.info(f"Making test request {i+1}")
        time.sleep(2)  # Simulate Reddit's rate limit
        requests += 1
    
    duration = (datetime.now() - start_time).total_seconds()
    logger.info(f"Made {requests} requests in {duration:.2f} seconds")
    logger.info(f"Average request rate: {requests/duration:.2f} requests/second")

if __name__ == "__main__":
    # Default URL for Faktory server
    faktory_server_url = "tcp://:password@localhost:7419"
    
    logger.info("Starting Reddit crawler Faktory tests")
    
    # Test rate limiting
    logger.info("\nTesting rate limiting:")
    test_rate_limiting()
    
    # Test job handling
    logger.info("\nTesting job handling:")
    produce_test_jobs(faktory_server_url)
    start_test_consumer(faktory_server_url)
