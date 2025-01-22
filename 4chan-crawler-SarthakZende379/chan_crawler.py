from chan_client import ChanClient
import logging
from pyfaktory import Client, Consumer, Job, Producer
import datetime
from pymongo import MongoClient
from dotenv import load_dotenv

# Logger setup
logger = logging.getLogger("4chan client")
logger.propagate = False
logger.setLevel(logging.INFO)
sh = logging.StreamHandler()
formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
sh.setFormatter(formatter)
logger.addHandler(sh)

load_dotenv()

import os

FAKTORY_SERVER_URL = "tcp://faktory:password@localhost:7419"
MONGO_URI = "mongodb://localhost:27017/"
DB_NAME = "chan_crawler"
COLLECTION_NAME = "4chan_posts"

"""
Return all the thread numbers from a catalog JSON object.
"""
def thread_numbers_from_catalog(catalog):
    thread_numbers = []
    for page in catalog:
        for thread in page["threads"]:
            thread_number = thread["no"]
            thread_numbers.append(thread_number)
    return thread_numbers

"""
Return thread numbers that existed in previous but don't exist in current.
"""
def find_dead_threads(previous_catalog_thread_numbers, current_catalog_thread_numbers):
    dead_thread_numbers = set(previous_catalog_thread_numbers).difference(
        set(current_catalog_thread_numbers)
    )
    return dead_thread_numbers

"""
Crawl a given thread and store its JSON data in MongoDB.
"""
def crawl_thread(board, thread_number):
    try:
        chan_client = ChanClient()
        thread_data = chan_client.get_thread(board, thread_number)

        logger.info(f"Thread: {board}/{thread_number}/:\n{thread_data}")

        # Connect to MongoDB
        mongo_client = MongoClient(MONGO_URI)
        db = mongo_client[DB_NAME]
        collection = db[COLLECTION_NAME]

        # Insert the thread data into MongoDB
        for post in thread_data["posts"]:
            post_number = post["no"]
            post_data = {
                "board": board,
                "thread_number": thread_number,
                "post_number": post_number,
                "data": post
            }
            collection.insert_one(post_data)
            logger.info(f"Inserted post number: {post_number}")

        mongo_client.close()

    except Exception as e:
        logger.error(f"Error while crawling thread {board}/{thread_number}: {e}")

"""
Fetch the catalog for a given board and determine which threads to crawl.
"""
def crawl_catalog(board, previous_catalog_thread_numbers=[]):
    try:
        chan_client = ChanClient()
        current_catalog = chan_client.get_catalog(board)

        current_catalog_thread_numbers = thread_numbers_from_catalog(current_catalog)
        dead_threads = find_dead_threads(
            previous_catalog_thread_numbers, current_catalog_thread_numbers
        )
        logger.info(f"Dead threads: {dead_threads}")

        # Enqueue crawl-thread jobs for each dead thread
        crawl_thread_jobs = []
        with Client(faktory_url=FAKTORY_SERVER_URL, role="producer") as client:
            producer = Producer(client=client)
            for dead_thread in dead_threads:
                job = Job(
                    jobtype="crawl-thread", args=(board, dead_thread), queue="crawl-thread"
                )
                crawl_thread_jobs.append(job)
            producer.push_bulk(crawl_thread_jobs)

        # Schedule another catalog crawl
        with Client(faktory_url=FAKTORY_SERVER_URL, role="producer") as client:
            producer = Producer(client=client)
            run_at = datetime.datetime.utcnow() + datetime.timedelta(minutes=5)
            run_at = run_at.isoformat()[:-7] + "Z"
            logger.info(f"Next catalog crawl scheduled at {run_at}")
            job = Job(
                jobtype="crawl-catalog",
                args=(board, current_catalog_thread_numbers),
                queue="crawl-catalog",
                at=str(run_at),
            )
            producer.push(job)

    except Exception as e:
        logger.error(f"Error while crawling catalog for board {board}: {e}")

if __name__ == "__main__":
    # Pull jobs off the Faktory queue and execute them continuously
    with Client(faktory_url=FAKTORY_SERVER_URL, role="consumer") as client:
        consumer = Consumer(
            client=client, queues=["crawl-catalog", "crawl-thread"], concurrency=5
        )
        consumer.register("crawl-catalog", crawl_catalog)
        consumer.register("crawl-thread", crawl_thread)
        consumer.run()
