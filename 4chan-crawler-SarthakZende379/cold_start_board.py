import logging
from pyfaktory import Client, Job, Producer
import sys

# Logger setup
logger = logging.getLogger("faktory test")
logger.propagate = False
logger.setLevel(logging.INFO)
sh = logging.StreamHandler()
formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
sh.setFormatter(formatter)
logger.addHandler(sh)

def cold_start_catalog_crawl(board, faktory_server_url):
    try:
        logger.info(f"Cold starting catalog crawl for board: {board}")
        
        with Client(faktory_url=faktory_server_url, role="producer") as client:
            producer = Producer(client=client)
            job = Job(jobtype="crawl-catalog", args=(board,), queue="crawl-catalog")
            producer.push(job)
            logger.info(f"Enqueued crawl-catalog job for board: {board}")
    except Exception as e:
        logger.error(f"Error while enqueuing crawl-catalog job: {e}")

if __name__ == "__main__":
    # Get the board name from command-line arguments or default to "pol"
    board = sys.argv[1] if len(sys.argv) > 1 else "pol"
    faktory_server_url = "tcp://faktory:password@localhost:7419"

    # Start the cold start process
    cold_start_catalog_crawl(board, faktory_server_url)
