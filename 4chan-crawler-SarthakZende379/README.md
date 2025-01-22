# 4chan Crawler

This repository is from live coding sessions from Binghamton University's 2024 CS 415/515 class.

## MongoDB Setup with Docker

To install and start MongoDB using Docker:

```
docker pull mongo
docker run -d --name mongodb -p 27017:27017 mongo
```

To access a MongoDB shell:

`docker exec -it mongodb mongosh`

## MongoDB Configuration

The default connection URL used in the code is:
`MONGO_URI="mongodb://localhost:27017/"`

The data is stored in a MongoDB database named `chan_crawler` with a collection named `4chan_posts`.

## Faktory

Install Faktory with Docker:

```
docker pull contribsys/faktory
```

Run Faktory:

```
docker run -it --name faktory \
  -v ~/projects/docker-disks/faktory-data:/var/lib/faktory/db \
  -e "FAKTORY_PASSWORD=password" \
  -p 127.0.0.1:7419:7419 \
  -p 127.0.0.1:7420:7420 \
  contribsys/faktory:latest \
  /faktory -b :7419 -w :7420
```

## Python Virtual Environment

It's recommended to use a virtual environment for Python dependencies:

1. Create a virtual environment:

   ```
   python -m venv ./env/dev
   ```

2. Activate the virtual environment:

   ```
   source env/dev/bin/activate
   ```

3. Install dependencies:

   ```
   pip install -r requirements.txt
   ```

4. Deactivate the virtual environment:

   ```
   deactivate
   ```

## Running the 4chan Crawler

### Cold Start the Crawler

To start the catalog crawling process for a specific board (e.g., "pol"):

```
python cold_start_board.py pol
```

### Running the Faktory Test Script

The `faktory-test.py` script can be used to test job scheduling with Faktory:

```
python faktory-test.py
```

### Running the Crawler Continuously

To continuously pull jobs from Faktory and execute them:

```
python chan_crawler.py
```

## Important Notes

- Ensure MongoDB and Faktory are running before starting the crawler.
- The MongoDB instance should be accessible at the configured `MONGO_URI`.
- Make sure to activate the virtual environment before running the scripts if dependencies are installed in a virtual environment.
```

