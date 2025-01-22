import logging
import requests
from pymongo import MongoClient
import time
from datetime import datetime, timezone

# Logger setup
logger = logging.getLogger("4chan client")
logger.propagate = False
logger.setLevel(logging.INFO)
sh = logging.StreamHandler()
formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
sh.setFormatter(formatter)
logger.addHandler(sh)

class ChanClient:
    API_BASE = "http://a.4cdn.org"
    MODERATE_HATESPEECH_TOKEN = "a494cf6fd08b41a49bb7f36650d209db"
    MAX_RETRIES = 3

    def __init__(self, mongo_uri="mongodb://localhost:27017/", db_name="chan_crawler", collection_name="4chan_posts"):
        # Set up MongoDB connection
        self.mongo_client = MongoClient(mongo_uri)
        self.db = self.mongo_client[db_name]
        self.collection = self.db[collection_name]

    def get_toxicity_score(self, text: str, retries: int = 0) -> dict:
        """Get toxicity score for text using ModerateHatespeech API"""
        if not text or len(text.strip()) == 0:
            logger.warning("Empty text provided for toxicity scoring")
            return {"class": "NA", "confidence": -1}
            
        try:
            url = "https://api.moderatehatespeech.com/api/v1/moderate/"
            response = requests.post(
                url,
                headers={
                    'Content-Type': 'application/json',
                    'Accept': 'application/json'
                },
                json={
                    "token": self.MODERATE_HATESPEECH_TOKEN,
                    "text": ' '.join(text.split())[:1000]
                },
                timeout=10
            )
            
            if response.status_code == 429:  # Rate limit
                wait_time = int(response.headers.get('Retry-After', 1))
                logger.warning(f"Toxicity API rate limit hit, waiting {wait_time} seconds")
                time.sleep(wait_time + 0.1)
                if retries < self.MAX_RETRIES:
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
            logger.error(f"Toxicity API Error: {str(e)}")
            if retries < self.MAX_RETRIES:
                time.sleep(1)
                return self.get_toxicity_score(text, retries + 1)
                
        return {"class": "NA", "confidence": -1}

    def get_thread(self, board, thread_number):
        """Get JSON for a given thread"""
        request_pieces = [board, "thread", f"{thread_number}.json"]
        api_call = self.build_request(request_pieces)
        json_data = self.execute_request(api_call)

        # Store the fetched data in MongoDB
        if json_data:
            self.store_data(json_data)

        return json_data

    def get_catalog(self, board):
        """Get catalog JSON for a given board"""
        request_pieces = [board, "catalog.json"]
        api_call = self.build_request(request_pieces)
        json_data = self.execute_request(api_call)

        # Store the fetched data in MongoDB
        if json_data:
            self.store_data(json_data)

        return json_data

    def build_request(self, request_pieces):
        """Build a request from pieces"""
        api_call = "/".join([self.API_BASE] + request_pieces)
        return api_call

    def execute_request(self, api_call):
        """Execute an HTTP request and return JSON"""
        try:
            resp = requests.get(api_call)
            logger.info(f"HTTP Status Code: {resp.status_code}")
            if resp.status_code == 200:
                return resp.json()
            else:
                logger.error(f"Failed to fetch data from {api_call}")
                return None
        except Exception as e:
            logger.error(f"Error during request execution: {e}")
            return None

    def store_data(self, data):
        """Store data in MongoDB with toxicity scoring"""
        try:
            # Process posts if they exist in the data
            if "posts" in data:
                # Add this import at the top of the file
                import random
                
                for post in data["posts"]:
                    # Get toxicity score for only 10% of posts
                    if "com" in post and random.random() < 0.1:
                        toxicity_result = self.get_toxicity_score(post["com"])
                        post["toxicity_class"] = toxicity_result["class"]
                        post["toxicity_score"] = toxicity_result["confidence"]
                        post["toxicity_processed_at"] = datetime.now(timezone.utc)
                
                # Insert the processed data into MongoDB
                self.collection.insert_one(data)
                post_count = len(data.get("posts", []))
                logger.info(f"Stored thread with {post_count} posts, sampling 10% for toxicity scores")
        except Exception as e:
            logger.error(f"Error storing data in MongoDB: {e}")

if __name__ == "__main__":
    client = ChanClient()
    json_data = client.get_thread("pol", 124205675)
    print(json_data)