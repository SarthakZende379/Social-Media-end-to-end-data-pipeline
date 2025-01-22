import logging
from pyfaktory import Client, Consumer, Job, Producer
import time
import random

# Logger setup
logger = logging.getLogger("faktory test")
logger.propagate = False
logger.setLevel(logging.INFO)
sh = logging.StreamHandler()
formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
sh.setFormatter(formatter)
logger.addHandler(sh)

def adder(x, y):
    logger.info(f"Adding {x} + {y} = {x + y}")
    # Simulate some processing time with random sleep
    sleep_for = random.randint(0, 10)
    time.sleep(sleep_for)
    logger.info(f"Finished sleeping for {sleep_for} seconds")

def produce_jobs(faktory_server_url):
    try:
        with Client(faktory_url=faktory_server_url, role="producer") as client:
            producer = Producer(client=client)

            # Generate 10 adder jobs
            jobs = []
            for job_num in range(10):
                job = Job(jobtype="adder", args=(job_num, 4), queue="default")
                jobs.append(job)

            producer.push_bulk(jobs)
            logger.info("Successfully enqueued 10 adder jobs")
    except Exception as e:
        logger.error(f"Error producing jobs: {e}")

def start_consumer(faktory_server_url):
    try:
        with Client(faktory_url=faktory_server_url, role="consumer") as client:
            consumer = Consumer(client=client, queues=["default"], concurrency=3)
            consumer.register("adder", adder)
            logger.info("Starting consumer to process adder jobs")
            consumer.run()
    except Exception as e:
        logger.error(f"Error starting consumer: {e}")

if __name__ == "__main__":
    # Default URL for a Faktory server running locally
    faktory_server_url = "tcp://:password@localhost:7419"

    # Produce jobs and start consumer
    produce_jobs(faktory_server_url)
    start_consumer(faktory_server_url)
