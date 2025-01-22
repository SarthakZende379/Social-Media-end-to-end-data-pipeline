Here is the finalized `README.md` in one block with the required formatting:

```markdown
# Reddit Crawler

This repository is designed for a Reddit crawler that continuously collects posts and comments from specified subreddits. It follows a similar pattern to a 4chan crawler setup, utilizing MongoDB for data storage and Faktory for job scheduling.

## MongoDB Setup with Docker

To install and start MongoDB using Docker:

```bash
docker pull mongo
docker run -d --name mongodb -p 27017:27017 mongo
```

To access a MongoDB shell:

```bash
docker exec -it mongodb mongosh
```

## MongoDB Configuration

The default connection URL used in the code is:
`MONGO_URI="mongodb://localhost:27017/"`

The data is stored in a MongoDB database named `reddit_crawler` with a collection named `reddit_posts`.

## Faktory

Install Faktory with Docker:

```bash
docker pull contribsys/faktory
```

Run Faktory:

```bash
docker run -it --name faktory \
  -v ~/projects/docker-disks/faktory-data:/var/lib/faktory/db \
  -e "FAKTORY_PASSWORD=password" \
  -p 127.0.0.1:7419:7419 \
  -p 127.0.0.1:7420:7420 \
  contribsys/faktory:latest \
  /faktory -b :7419 -w :7420
```

## Python Virtual Environment

It is recommended to use a virtual environment for Python dependencies:

1. Create a virtual environment:

   python -m venv ./env/dev


2. Activate the virtual environment:

   source env/dev/bin/activate


3. Install dependencies:

   pip install -r requirements.txt


4. Deactivate the virtual environment when done:

   deactivate
   

## Running the Reddit Crawler

### Configuration File

Set up the `config.json` file to specify subreddits and other settings. Example configuration:

```json
{
    "subreddits": [
        "neutralpolitics",
        "conservative",
        "democrat",
        "republican",
        "politicaldiscussion",
        "politics"
    ],
    "update_interval": 300,
    "mongodb": {
        "uri": "mongodb://localhost:27017/",
        "db": "reddit_crawler",
        "collection": "reddit_posts"
    },
    "faktory": {
        "url": "tcp://faktory:password@localhost:7419"
    }
}
```

### Cold Start the Crawler

To start crawling for a specific subreddit (e.g., "politics"):

```bash
python cold_start_subreddit.py politics
```

### Running the Faktory Test Script

The `faktory-test.py` script can be used to test job scheduling with Faktory:

```bash
python faktory-test.py
```

### Running the Crawler Continuously

To continuously pull jobs from Faktory and execute them:

```bash
python reddit_crawler.py
```

## Important Notes

- Ensure MongoDB and Faktory are running before starting the crawler.
- The MongoDB instance should be accessible at the configured `MONGO_URI`.
