import logging
from pyfaktory import Client, Job, Producer
import json

# Logger setup
logger = logging.getLogger("reddit cold start")
logger.propagate = False
logger.setLevel(logging.INFO)
sh = logging.StreamHandler()
formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
sh.setFormatter(formatter)
logger.addHandler(sh)

# Queue name specific to Reddit
REDDIT_SUBREDDIT_QUEUE = 'reddit-crawl-subreddit'

def cold_start_reddit_crawl():
    try:
        # Load configuration
        with open('config.json', 'r') as f:
            config = json.load(f)
        
        logger.info("Starting Reddit crawler cold start")
        
        # Create jobs for each subreddit
        with Client(faktory_url=config['faktory']['url'], role='producer') as client:
            producer = Producer(client=client)
            
            for subreddit in config['subreddits']:
                job = Job(
                    jobtype='reddit-crawl-subreddit',  # Updated jobtype
                    args=(subreddit,),
                    queue=REDDIT_SUBREDDIT_QUEUE  # Using Reddit-specific queue
                )
                producer.push(job)
                logger.info(f"Enqueued crawl job for r/{subreddit}")
                
    except Exception as e:
        logger.error(f"Error during cold start: {e}")

if __name__ == "__main__":
    cold_start_reddit_crawl()