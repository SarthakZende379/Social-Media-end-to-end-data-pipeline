import logging
from logging.handlers import RotatingFileHandler
import requests
from pymongo import MongoClient
from datetime import datetime, timezone
import time
import os

class RedditClient:
    REDDIT_BASE_URL = "https://oauth.reddit.com"
    AUTH_URL = "https://www.reddit.com/api/v1/access_token"
    MODERATE_HATESPEECH_TOKEN = "a494cf6fd08b41a49bb7f36650d209db" 

    def __init__(self, config, mongo_uri="mongodb://localhost:27017/", db_name="reddit_crawler"):
        # Setup logging
        self.setup_logging()
        
        # Set up MongoDB connection
        self.mongo_client = MongoClient(mongo_uri)
        self.db = self.mongo_client[db_name]
        self.posts_collection = self.db[config["mongodb"]["collections"]["posts"]]
        self.comments_collection = self.db[config["mongodb"]["collections"]["comments"]]
        self.failed_posts_collection = self.db[config["mongodb"]["collections"]["failed_posts"]]
        self.failed_comments_collection = self.db[config["mongodb"]["collections"]["failed_comments"]]
        
        # Reddit API credentials
        self.client_id = config["reddit"]["client_id"]
        self.client_secret = config["reddit"]["client_secret"]
        self.username = config["reddit"]["username"]
        self.password = config["reddit"]["password"]
        self.user_agent = config["reddit"]["user_agent"]
        
        # Settings
        self.max_retry_attempts = config["crawl_settings"]["max_retry_attempts"]
        self.rate_limit_buffer = config["crawl_settings"]["rate_limit_buffer"]
        
        # Authentication state
        self.access_token = None
        self.token_expires_at = 0
        self.rate_limit_remaining = None
        self.rate_limit_reset = None
        
        # Initial authentication
        self.authenticate()

    def setup_logging(self):
        """Setup rotating log file handler"""
        # Create logs directory if it doesn't exist
        os.makedirs('logs', exist_ok=True)
        
        self.logger = logging.getLogger("reddit_client")
        self.logger.setLevel(logging.INFO)
        
        # Remove existing handlers
        self.logger.handlers = []
        
        # Add rotating file handler
        handler = RotatingFileHandler(
            'logs/reddit_client.log',
            maxBytes=10*1024*1024,  # 10MB
            backupCount=5
        )
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - [%(filename)s:%(lineno)d] - %(message)s'
        )
        handler.setFormatter(formatter)
        self.logger.addHandler(handler)
        
        # Add console handler
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(formatter)
        self.logger.addHandler(console_handler)

    def authenticate(self):
        """Handle Reddit OAuth2 authentication"""
        try:
            auth = requests.auth.HTTPBasicAuth(self.client_id, self.client_secret)
            data = {
                'grant_type': 'password',
                'username': self.username,
                'password': self.password
            }
            headers = {'User-Agent': self.user_agent}
            
            response = requests.post(self.AUTH_URL, auth=auth, data=data, headers=headers)
            
            if response.status_code != 200:
                self.logger.error(f"Authentication failed: {response.text}")
                self.logger.error(f"******************************: {response}")
                self.logger.error(f"******************************: {response.status_code}")
                response.raise_for_status()
            
            token_data = response.json()
            self.access_token = token_data['access_token']
            self.token_expires_at = time.time() + token_data['expires_in']
            self.logger.info("Successfully authenticated with Reddit API")
            
        except Exception as e:
            self.logger.error(f"Authentication error: {e}")
            raise

    def check_token(self):
        """Check and refresh token if needed"""
        if time.time() >= self.token_expires_at - 60:
            self.authenticate()

    def get_headers(self):
        """Get headers for API requests"""
        self.check_token()
        return {
            'Authorization': f'Bearer {self.access_token}',
            'User-Agent': self.user_agent
        }

    def handle_rate_limit(self, headers):
        """Handle rate limiting based on Reddit API headers"""
        try:
            self.rate_limit_remaining = int(headers.get('x-ratelimit-remaining', 0))
            self.rate_limit_reset = float(headers.get('x-ratelimit-reset', 0))
            
            if self.rate_limit_remaining < self.rate_limit_buffer:
                sleep_time = max(self.rate_limit_reset, 10)
                self.logger.error(f"Rate limit headers: {headers}")
                self.logger.error(f"******************************: Remaining: {self.rate_limit_remaining}")
                self.logger.error(f"******************************: Reset: {self.rate_limit_reset}")
                time.sleep(sleep_time)
        except Exception as e:
            self.logger.error(f"Error handling rate limit: {e}")

    def store_failed_post(self, post_id, subreddit, error_type):
        """Store failed post for retry"""
        try:
            self.failed_posts_collection.update_one(
                {'_id': post_id},
                {
                    '$set': {
                        'last_attempt': datetime.now(timezone.utc),
                        'error_type': str(error_type)
                    },
                    '$inc': {'attempt_count': 1},
                    '$setOnInsert': {
                        'subreddit': subreddit,
                        'first_seen': datetime.now(timezone.utc)
                    }
                },
                upsert=True
            )
        except Exception as e:
            self.logger.error(f"Failed to store post {post_id}")
            self.logger.error(f"******************************: Error: {e}")

    def store_failed_comment(self, comment_id, post_id, subreddit, error_type):
        """Store failed comment for retry"""
        try:
            self.failed_comments_collection.update_one(
                {'_id': comment_id},
                {
                    '$set': {
                        'last_attempt': datetime.now(timezone.utc),
                        'error_type': str(error_type)
                    },
                    '$inc': {'attempt_count': 1},
                    '$setOnInsert': {
                        'post_id': post_id,
                        'subreddit': subreddit,
                        'first_seen': datetime.now(timezone.utc)
                    }
                },
                upsert=True
            )
            self.logger.info(f"Stored failed comment {comment_id} for retry")
        except Exception as e:
            self.logger.error(f"Error storing failed comment {comment_id}: {str(e)}")

    def get_failed_posts(self, max_attempts=None):
        """Get posts that need to be retried"""
        if max_attempts is None:
            max_attempts = self.max_retry_attempts
            
        return list(self.failed_posts_collection.find({
            'attempt_count': {'$lt': max_attempts}
        }).limit(50))

    def get_failed_comments(self, max_attempts=None):
        """Get comments that need to be retried"""
        if max_attempts is None:
            max_attempts = self.max_retry_attempts
            
        return list(self.failed_comments_collection.find({
            'attempt_count': {'$lt': max_attempts}
        }).limit(50))

    def remove_failed_post(self, post_id):
        """Remove succeeded post from failed collection"""
        try:
            self.failed_posts_collection.delete_one({'_id': post_id})
            self.logger.info(f"Removed successful post {post_id} from failed posts")
        except Exception as e:
            self.logger.error(f"Error removing failed post {post_id}: {str(e)}")

    def remove_failed_comment(self, comment_id):
        """Remove succeeded comment from failed collection"""
        try:
            self.failed_comments_collection.delete_one({'_id': comment_id})
            self.logger.info(f"Removed successful comment {comment_id} from failed comments")
        except Exception as e:
            self.logger.error(f"Error removing failed comment {comment_id}: {str(e)}")

    def get_subreddit_posts(self, subreddit, limit=1000):
        """Fetch recent posts with pagination"""
        all_posts = []
        after_token = None
        
        while len(all_posts) < limit:
            try:
                url = f"{self.REDDIT_BASE_URL}/r/{subreddit}/new"
                params = {
                    'limit': min(100, limit - len(all_posts)),
                    'after': after_token,
                    'sort': 'new'       #added later on to get new posts
                }
                
                response = requests.get(url, headers=self.get_headers(), params=params)
                
                if response.status_code == 429:  # Rate limit hit
                    self.logger.error(f"Rate limit reached: {response.text}")
                    self.logger.error(f"******************************: {response}")
                    self.logger.error(f"******************************: {response.status_code}")
                    time.sleep(60)
                    continue
                
                if response.status_code != 200:
                    self.logger.error(f"Failed to fetch posts: {response.text}")
                    self.logger.error(f"******************************: {response}")
                    self.logger.error(f"******************************: {response.status_code}")
                    time.sleep(30)
                    continue
                
                data = response.json()
                posts = data['data']['children']
                
                if not posts:
                    break
                    
                for post in posts:
                    post_data = post['data']
                    post_data['_id'] = post_data['id']
                    post_data['subreddit'] = subreddit
                    post_data['collected_at'] = datetime.now(timezone.utc)
                    
                    try:
                        self.posts_collection.update_one(
                            {'_id': post_data['_id']},
                            {'$set': post_data},
                            upsert=True
                        )
                        all_posts.append(post_data['id'])
                    except Exception as e:
                        self.logger.error(f"Error storing post {post_data['id']}: {e}")
                
                after_token = data['data'].get('after')
                if not after_token:
                    break
                    
                self.logger.info(f"Collected {len(posts)} posts from r/{subreddit}")
                    
            except Exception as e:
                self.logger.error(f"Unexpected error: {e}")
                break
        
        return all_posts

    def get_post_comments(self, post_id, subreddit):
        """Fetch comments for a specific post"""
        try:
            url = f"{self.REDDIT_BASE_URL}/r/{subreddit}/comments/{post_id}"
            response = requests.get(url, headers=self.get_headers())
            
            if response.status_code == 429:
                self.logger.error(f"Rate limit reached: {response.text}")
                self.logger.error(f"******************************: {response}")
                self.logger.error(f"******************************: {response.status_code}")
                time.sleep(60)
                return False
            
            post_data = response.json()
            
            def process_comments(comments, parent_id=None):
                for comment in comments:
                    if comment['kind'] == 't1':  # Regular comment
                        try:
                            comment_data = comment['data']
                            comment_data['_id'] = comment_data['id']
                            comment_data['post_id'] = post_id
                            comment_data['parent_id'] = parent_id
                            comment_data['subreddit'] = subreddit
                            comment_data['collected_at'] = datetime.now(timezone.utc)
                            
                            # Add toxicity scoring for only 10% of comments
                            import random
                            if comment_data.get('body') and random.random() < 0.1:
                                toxicity_result = self.get_toxicity_score(comment_data['body'])
                                comment_data['toxicity_class'] = toxicity_result['class']
                                comment_data['toxicity_score'] = toxicity_result['confidence']
                                comment_data['processed_at'] = datetime.now(timezone.utc)
                            
                            self.comments_collection.update_one(
                                {'_id': comment_data['_id']},
                                {'$set': comment_data},
                                upsert=True
                            )
                            
                            if comment_data.get('replies'):
                                replies = comment_data['replies'].get('data', {}).get('children', [])
                                process_comments(replies, comment_data['id'])
                                
                        except Exception as e:
                            self.logger.error(f"Error processing comment {comment_data.get('id', 'unknown')}: {e}")
                            self.store_failed_comment(...)
            
            # Process all comments
            if len(post_data) > 1:
                comments = post_data[1]['data']['children']
                process_comments(comments)
                return True
            
            return True
            
        except Exception as e:
            self.logger.error(f"Error fetching comments for post {post_id}: {e}")
            return False
    
    #Added new function for Live toxicity integration
    def get_toxicity_score(self, text: str, retries: int = 0) -> dict:
        """Get toxicity score for text using ModerateHatespeech API"""
        # Add this constant at the top of RedditClient class
        MODERATE_HATESPEECH_TOKEN = "a494cf6fd08b41a49bb7f36650d209db"
        
        if not text or len(text.strip()) == 0:
            self.logger.warning("Empty text provided for toxicity scoring")
            return {"class": "NA", "confidence": -1}
            
        try:
            url = "https://api.moderatehatespeech.com/api/v1/moderate/"
            
            # Log the actual request
            request_data = {
                "token": self.MODERATE_HATESPEECH_TOKEN,  # Use class constant instead of config
                "text": ' '.join(text.split())[:1000]
            }
            self.logger.info(f"Sending toxicity request with text: {text[:100]}...")
            
            response = requests.post(
                url,
                headers={
                    'Content-Type': 'application/json',
                    'Accept': 'application/json'
                },
                json=request_data,
                timeout=10
            )
            
            # Log the raw response
            self.logger.info(f"Response status: {response.status_code}")
            self.logger.info(f"Response content: {response.text}")
            
            if response.status_code == 429:  # Rate limit
                wait_time = int(response.headers.get('Retry-After', 1))
                self.logger.warning(f"Toxicity API rate limit hit, waiting {wait_time} seconds")
                time.sleep(wait_time + 0.1)
                if retries < 3:  # Use hardcoded max retries
                    return self.get_toxicity_score(text, retries + 1)
                return {"class": "NA", "confidence": -1}
                
            response.raise_for_status()
            result = response.json()
            
            # Log the parsed result
            self.logger.info(f"Parsed API result: {result}")
            
            if result.get('response') == "Success":
                toxicity_result = {
                    'class': result['class'],
                    'confidence': float(result['confidence'])
                }
                self.logger.info(f"Successfully scored toxicity: {toxicity_result}")
                return toxicity_result
                
            self.logger.error(f"Unexpected API response format: {result}")
                
        except requests.exceptions.Timeout:
            self.logger.error("Toxicity API timeout")
            if retries < 3:  # Use hardcoded max retries
                time.sleep(1)
                return self.get_toxicity_score(text, retries + 1)
        except Exception as e:
            self.logger.error(f"Toxicity API Error: {str(e)}")
            self.logger.error(f"Error type: {type(e).__name__}")
            
        return {"class": "NA", "confidence": -1}