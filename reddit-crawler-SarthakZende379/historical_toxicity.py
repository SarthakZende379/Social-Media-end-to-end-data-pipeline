import requests
from pymongo import MongoClient, UpdateMany
from datetime import datetime, timezone, timedelta
import json
import time
import logging
from concurrent.futures import ThreadPoolExecutor, as_completed
import threading
import gc
import psutil
from tqdm import tqdm
from typing import List, Dict, Any
import sys
from queue import Queue

# Enhanced logging configuration
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('toxicity_processor.log'),
        logging.StreamHandler(sys.stdout)
    ]
)

class ToxicityProcessor:
    def __init__(self):
        with open('config.json', 'r') as f:
            self.config = json.load(f)
            
        # Connection pooling
        self.mongo_client = MongoClient(
            self.config['mongodb']['uri'],
            maxPoolSize=50,
            minPoolSize=10,
            maxIdleTimeMS=45000
        )
        self.db = self.mongo_client['reddit_crawler']
        self.comments_collection = self.db['reddit_comments']
        
        # API setup
        self.api_token = self.config['moderate_hatespeech']['api_token']
        
        # Thread-safe queues and counters
        self.result_queue = Queue(maxsize=1000)
        self.stats_lock = threading.Lock()
        self.stats = {
            'processed': 0,
            'errors': 0,
            'rate_limits': 0,
            'start_time': datetime.now()
        }
        
        # Processing settings
        self.batch_size = 50  # Number of comments per MongoDB batch
        self.thread_count = 6  # Number of worker threads
        
    def get_toxicity_score(self, text: str, retries: int = 0) -> Dict[str, Any]:
        if not text or len(text.strip()) == 0:
            return {"class": "NA", "confidence": -1}
            
        url = "https://api.moderatehatespeech.com/api/v1/moderate/"
        
        try:
            response = requests.post(
                url,
                headers={
                    'Content-Type': 'application/json',
                    'Accept': 'application/json'
                },
                json={
                    "token": self.api_token,
                    "text": ' '.join(text.split())[:1000]
                },
                timeout=10
            )
            
            if response.status_code == 429:  # Rate limit
                with self.stats_lock:
                    self.stats['rate_limits'] += 1
                wait_time = int(response.headers.get('Retry-After', 1))
                time.sleep(wait_time + 0.1)
                if retries < 3:
                    return self.get_toxicity_score(text, retries + 1)
                return {"class": "NA", "confidence": -1}
                
            response.raise_for_status()
            result = response.json()
            
            if result.get('response') == "Success":
                return {
                    'class': result['class'],
                    'confidence': float(result['confidence'])
                }
                
        except Exception as e:
            with self.stats_lock:
                self.stats['errors'] += 1
            logging.error(f"API Error: {str(e)}")
            
            if retries < 3 and isinstance(e, requests.exceptions.Timeout):
                time.sleep(1)
                return self.get_toxicity_score(text, retries + 1)
                
        return {"class": "NA", "confidence": -1}

    def process_comments(self, comments: List[Dict]) -> None:
        """Process a batch of comments in parallel"""
        try:
            results = []
            futures = {}
            
            with ThreadPoolExecutor(max_workers=self.thread_count) as executor:
                # Submit all tasks
                for comment in comments:
                    if not comment.get('body'):
                        continue
                    future = executor.submit(self.get_toxicity_score, comment['body'])
                    futures[future] = comment['_id']
                
                # Process results as they complete
                for future in as_completed(futures):
                    comment_id = futures[future]
                    try:
                        result = future.result()
                        results.append({
                            '_id': comment_id,
                            'result': result
                        })
                        
                        with self.stats_lock:
                            self.stats['processed'] += 1
                            
                    except Exception as e:
                        logging.error(f"Error processing comment {comment_id}: {str(e)}")
                        with self.stats_lock:
                            self.stats['errors'] += 1
            
            # Batch update MongoDB
            if results:
                updates = [
                    UpdateMany(
                        {"_id": r['_id']},
                        {
                            "$set": {
                                "toxicity_class": r['result']['class'],
                                "toxicity_score": r['result']['confidence'],
                                "processed_at": datetime.now(timezone.utc)
                            }
                        }
                    ) for r in results
                ]
                self.comments_collection.bulk_write(updates, ordered=False)
                
        except Exception as e:
            logging.error(f"Batch processing error: {str(e)}")

    def process_date_range(self, start_date: datetime, end_date: datetime) -> None:
        query = {
            "created_utc": {
                "$gte": start_date.timestamp(),
                "$lt": end_date.timestamp()
            },
            "$or": [
                {"toxicity_score": {"$exists": False}},
                {"toxicity_score": -1}
            ]
        }
        
        total_comments = self.comments_collection.count_documents(query)
        processed = 0
        
        with tqdm(total=total_comments, desc=f"Processing {start_date.date()}") as pbar:
            while processed < total_comments:
                if psutil.virtual_memory().available < 500 * 1024 * 1024:
                    logging.warning("Low memory - waiting 30 seconds")
                    time.sleep(30)
                    continue
                    
                comments = list(self.comments_collection.find(
                    query,
                    {"_id": 1, "body": 1}
                ).limit(self.batch_size))
                
                if not comments:
                    break
                    
                self.process_comments(comments)
                processed += len(comments)
                pbar.update(len(comments))
                
                # Adjust sleep time based on rate limits
                sleep_time = 0.1 if self.stats['rate_limits'] == 0 else 0.5
                time.sleep(sleep_time)
                
                # Force garbage collection periodically
                if processed % 1000 == 0:
                    gc.collect()

def main():
    processor = ToxicityProcessor()
    
    # Process Nov 6 (election day) first
    dates_to_process = [
        (datetime(2024, 11, 6, tzinfo=timezone.utc), datetime(2024, 11, 7, tzinfo=timezone.utc)),
        (datetime(2024, 11, 4, tzinfo=timezone.utc), datetime(2024, 11, 5, tzinfo=timezone.utc)),
        (datetime(2024, 11, 5, tzinfo=timezone.utc), datetime(2024, 11, 6, tzinfo=timezone.utc)),
        (datetime(2024, 11, 7, tzinfo=timezone.utc), datetime(2024, 11, 8, tzinfo=timezone.utc))
    ]
    
    try:
        for start_date, end_date in dates_to_process:
            logging.info(f"\nProcessing date range: {start_date.date()} to {end_date.date()}")
            processor.process_date_range(start_date, end_date)
            
            # Print stats after each day
            elapsed = datetime.now() - processor.stats['start_time']
            rate = processor.stats['processed'] / elapsed.total_seconds() * 3600
            logging.info(
                f"\nProcessing Statistics:\n"
                f"Total Processed: {processor.stats['processed']:,}\n"
                f"Error Count: {processor.stats['errors']:,}\n"
                f"Rate Limits Hit: {processor.stats['rate_limits']:,}\n"
                f"Processing Rate: {rate:.1f} comments/hour\n"
                f"Elapsed Time: {elapsed}\n"
            )
            
    except KeyboardInterrupt:
        logging.info("\nGracefully shutting down...")
        
    except Exception as e:
        logging.error(f"Fatal error: {str(e)}")
        
    finally:
        logging.info("\nFinal Statistics:")
        elapsed = datetime.now() - processor.stats['start_time']
        rate = processor.stats['processed'] / elapsed.total_seconds() * 3600
        logging.info(
            f"Total Processed: {processor.stats['processed']:,}\n"
            f"Error Count: {processor.stats['errors']:,}\n"
            f"Rate Limits Hit: {processor.stats['rate_limits']:,}\n"
            f"Final Rate: {rate:.1f} comments/hour\n"
            f"Total Time: {elapsed}"
        )

if __name__ == "__main__":
    main()