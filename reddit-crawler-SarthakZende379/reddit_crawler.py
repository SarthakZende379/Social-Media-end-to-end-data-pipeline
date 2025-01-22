import logging
from logging.handlers import RotatingFileHandler
from pyfaktory import Client, Consumer, Job, Producer
import json
import datetime
import time
import os
from reddit_client import RedditClient
from datetime import datetime, timedelta, timezone

# Queue constants
REDDIT_SUBREDDIT_QUEUE = 'reddit-crawl-subreddit'
REDDIT_COMMENTS_QUEUE = 'reddit-crawl-comments'
REDDIT_RETRY_QUEUE = 'reddit-retry-queue'
REDDIT_COMMENTS_RETRY_QUEUE = 'reddit-comments-retry-queue'

def setup_logging():
    """Setup rotating log file for crawler"""
    # Create logs directory if it doesn't exist
    os.makedirs('logs', exist_ok=True)
    
    logger = logging.getLogger('reddit_crawler')
    logger.setLevel(logging.INFO)
    
    # Remove existing handlers
    logger.handlers = []
    
    # Add rotating file handler
    handler = RotatingFileHandler(
        'logs/reddit_crawler.log',
        maxBytes=10*1024*1024,  # 10MB
        backupCount=5
    )
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - [%(filename)s:%(lineno)d] - %(message)s'
    )
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    
    # Add console handler
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)
    
    return logger

# Setup logger
logger = setup_logging()

# Load configuration
try:
    with open('config.json', 'r') as f:
        config = json.load(f)
    logger.info("Successfully loaded configuration")
except Exception as e:
    logger.error(f"Error loading configuration: {str(e)}")
    raise

def crawl_subreddit(subreddit):
    """Crawl a subreddit for new posts"""
    logger.info(f"Starting crawl for r/{subreddit}")
    try:
        reddit_client = RedditClient(config)
        post_ids = reddit_client.get_subreddit_posts(
            subreddit,
            limit=config['crawl_settings']['post_limit']
        )
        
        if not post_ids:
            logger.error(f"No posts collected from r/{subreddit}")
            logger.error(f"******************************: Scheduling retry")
            schedule_next_crawl(subreddit, delay_minutes=5)  # Retry sooner if no posts
            return
        
        logger.info(f"Collected {len(post_ids)} posts from r/{subreddit}")
        
        # Enqueue comment jobs in batches
        with Client(faktory_url=config['faktory']['url'], role='producer') as client:
            producer = Producer(client=client)
            
            for i in range(0, len(post_ids), 50):
                batch = post_ids[i:i+50]
                try:
                    comment_jobs = [
                        Job(
                            jobtype='reddit-crawl-comments',
                            args=(post_id, subreddit),
                            queue=REDDIT_COMMENTS_QUEUE
                        )
                        for post_id in batch
                    ]
                    producer.push_bulk(comment_jobs)
                    logger.info(f"Enqueued {len(batch)} comment jobs for r/{subreddit}")
                except Exception as e:
                    logger.error(f"Failed to enqueue comment jobs")
                    logger.error(f"******************************: Error: {e}")
                    logger.error(f"******************************: Batch size: {len(batch)}")
                time.sleep(2)
        
        schedule_next_crawl(subreddit)
        
    except Exception as e:
        logger.error(f"Error in crawl_subreddit")
        logger.error(f"******************************: {e}")
        schedule_next_crawl(subreddit, delay_minutes=15)

def crawl_comments(post_id, subreddit):
    """Process comments for a specific post"""
    try:
        reddit_client = RedditClient(config)
        success = reddit_client.get_post_comments(post_id, subreddit)
        
        if not success:
            logger.error(f"Failed to crawl comments for post {post_id}")
            logger.error(f"******************************: Adding to failed posts")
            reddit_client.store_failed_post(post_id, subreddit, "Comment crawl failed")
            
    except Exception as e:
        logger.error(f"Error processing comments")
        logger.error(f"******************************: Post ID: {post_id}")
        logger.error(f"******************************: Error: {e}")


def process_retry_queue():
    """Process failed posts retry queue"""
    try:
        reddit_client = RedditClient(config)
        failed_posts = reddit_client.get_failed_posts(
            config['crawl_settings']['max_retry_attempts']
        )
        
        for post in failed_posts:
            try:
                success = reddit_client.get_post_comments(
                    post['_id'],
                    post['subreddit']
                )
                
                if success:
                    reddit_client.remove_failed_post(post['_id'])
                    logger.info(f"Successfully processed failed post {post['_id']}")
                else:
                    logger.error(f"Failed to process post in retry queue")
                    logger.error(f"******************************: Post ID: {post['_id']}")
                    
            except Exception as e:
                logger.error(f"Error in retry processing")
                logger.error(f"******************************: Post ID: {post['_id']}")
                logger.error(f"******************************: Error: {e}")
        
        schedule_retry_batch()
        
    except Exception as e:
        logger.error(f"Error processing retry queue")
        logger.error(f"******************************: Error: {e}")
        schedule_retry_batch(delay_minutes=15)

def schedule_next_crawl(subreddit, delay_minutes=None):
    """Schedule the next crawl for a subreddit"""
    if delay_minutes is None:
        delay_minutes = config['crawl_settings']['subreddit_interval_minutes']
    
    try:
        with Client(faktory_url=config['faktory']['url'], role='producer') as client:
            producer = Producer(client=client)
            run_at = (datetime.now(timezone.utc) + timedelta(minutes=delay_minutes)).strftime('%Y-%m-%dT%H:%M:%SZ')
            
            job = Job(
                jobtype='reddit-crawl-subreddit',
                args=(subreddit,),
                queue=REDDIT_SUBREDDIT_QUEUE,
                at=run_at
            )
            producer.push(job)
            logger.info(f"Scheduled next crawl for r/{subreddit} at {run_at}")
            
    except Exception as e:
        logger.error(f"Failed to schedule next crawl")
        logger.error(f"******************************: Subreddit: {subreddit}")
        logger.error(f"******************************: Error: {e}")

def schedule_retry_batch(delay_minutes=None):
    """Schedule next retry batch"""
    if delay_minutes is None:
        delay_minutes = config['crawl_settings']['retry_interval_minutes']
    
    try:
        with Client(faktory_url=config['faktory']['url'], role='producer') as client:
            producer = Producer(client=client)
            # Use timezone-aware datetime in RFC3339 format
            run_at = (datetime.now(timezone.utc) + timedelta(minutes=delay_minutes)).strftime('%Y-%m-%dT%H:%M:%SZ')
            
            job = Job(
                jobtype='reddit-retry-posts',
                queue=REDDIT_RETRY_QUEUE,
                at=run_at  # Already RFC3339-compliant; no need for .isoformat()
            )
            producer.push(job)
            logger.info(f"Scheduled next retry batch at {run_at}")
            
    except Exception as e:
        logger.error(f"Error scheduling retry batch: {str(e)}")

if __name__ == "__main__":
    logger.info("Starting Reddit crawler")
    
    try:
        with Client(faktory_url=config['faktory']['url'], role='consumer') as client:
            consumer = Consumer(
                client=client,
                queues=[
                    REDDIT_SUBREDDIT_QUEUE,
                    REDDIT_COMMENTS_QUEUE,
                    REDDIT_RETRY_QUEUE,
                    REDDIT_COMMENTS_RETRY_QUEUE
                ],
                concurrency=5
            )
            
            consumer.register('reddit-crawl-subreddit', crawl_subreddit)
            consumer.register('reddit-crawl-comments', crawl_comments)
            consumer.register('reddit-retry-posts', process_retry_queue)
            
            logger.info("Reddit crawler initialized and ready to process jobs")
            consumer.run()
            
    except Exception as e:
        logger.error(f"Fatal error in crawler: {str(e)}")
        raise