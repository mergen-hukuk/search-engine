# EMSAL Court Decision Scraper

This module contains a set of scripts designed to scrape court decisions from the EMSAL UYAP system (Turkish Court Decision Database) using Tor for anonymity and IP rotation.

## Components

### Main Scripts

1. `scrape.py`
   - Main scraping script for paginated search results
   - Uses pycurl for making HTTP requests
   - Implements user agent rotation
   - Saves search results as JSON files
   - Changes Tor circuit every 20 pages

2. `get_doc_scraper.py`
   - Asynchronous document fetcher
   - Uses aiohttp for concurrent requests
   - Handles batches of document IDs (69 concurrent requests)
   - Implements automatic retry mechanism on failure
   - Tracks request statistics and response times

3. `ip_handler.py`
   - Manages Tor circuit changes
   - Checks for rate limiting
   - Provides proxy session management
   - Supports country-specific exit nodes (TR, US, GB, DE, FR, IT, ES, CA)

### Utility Scripts

4. `count.sh`
   - Monitors the number of downloaded files
   - Shows real-time progress with file count changes
   - Updates every 10 seconds

5. `run.sh`
   - Manages the execution of the document scraper
   - Implements automatic restart on specific error codes (35)
   - Handles graceful termination

## Prerequisites

- Python 3.7+
- Tor service running on port 9050 (control port 9051)
- Required Python packages:
  - aiohttp
  - aiofiles
  - pycurl
  - stem
  - random-user-agent
  - aiohttp_socks

## Configuration

The system uses several configuration parameters:

- Batch size: 69 concurrent requests
- Document ID range: 2,000,000 to 10,000,000
- Tor circuit rotation:
  - On rate limiting detection
  - When average response time exceeds 1 second
  - Every 20 pages in search results

## Usage

1. Start the Tor service
2. Run the search results scraper:
   ```bash
   python3 scrape.py
   ```

3. Run the document scraper:
   ```bash
   ./run.sh
   ```

4. Monitor progress:
   ```bash
   ./count.sh
   ```

## Data Storage

- Search results: `./data/{year}/pages/`
- Documents: `./docs/`
- Document tracking: `existing_docs.txt`

## Error Handling

- Automatic retry on CAPTCHA detection
- Circuit rotation on rate limiting
- Response time monitoring
- Batch failure recovery
- Graceful termination with state preservation

## Notes

- The system uses Tor for anonymity and IP rotation
- Implements various anti-detection measures:
  - User agent rotation
  - Request rate limiting
  - Circuit rotation
  - Multiple exit node countries
- Saves progress to allow for interrupted/resumed scraping sessions 