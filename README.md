# Turkish Legal Document Search Engine

A comprehensive system for scraping, processing, and searching Turkish legal documents using modern NLP and vector search techniques.

## Project Overview

This project consists of three main components:

1. **Document Scraping**: Automated scraping of court decisions from EMSAL UYAP system
2. **Document Processing**: Converting HTML documents to markdown and extracting keywords
3. **Vector Search**: Generating embeddings and enabling semantic search using Milvus

## System Architecture

- **Web Scraping**: Python + Tor for anonymous scraping
- **Processing Pipeline**: Apache Spark + Spark NLP
- **Vector Database**: Milvus + Ollama for embeddings
- **Infrastructure**: Docker support for containerization

## Components

### 1. EMSAL Scraper (`emsal_scraper-dev/`)
- `scrape.py`: Main scraping script for search results
- `get_doc_scraper.py`: Asynchronous document fetcher
- `ip_handler.py`: Tor circuit management
- Supporting scripts: `count.sh`, `run.sh`

### 2. Document Processing (`src/`)
- `md_convert.py`: HTML to Markdown conversion
- `keyword_pipeline.py`: Keyword extraction using Spark NLP
- `milvus_spark.py`: Document embedding generation and storage
- `ollama_kanun.py`: Law reference extraction

## Prerequisites

- Python 3.7+
- Apache Spark
- Milvus
- Ollama
- Tor service (for scraping)
- Docker (optional)

## Installation

1. Clone the repository:
   ```bash
   git clone <repository-url>
   cd search-engine
   ```

2. Create and activate virtual environment:
   ```bash
   make venv
   source venv/bin/activate
   ```

3. Install dependencies:
   ```bash
   make install
   ```

4. Set up environment variables:
   ```bash
   cp .env.example .env
   # Edit .env with your configuration
   ```

## Usage

### 1. Document Scraping

```bash
cd emsal_scraper-dev
./run.sh
```

Monitor progress:
```bash
./count.sh
```

### 2. Document Processing

Convert HTML to Markdown:
```bash
python src/md_convert.py
```

Extract keywords:
```bash
python src/keyword_pipeline.py
```

### 3. Vector Search Setup

Process and store embeddings:
```bash
python src/milvus_spark.py
```

Stop Milvus server:
```bash
./stop_milvus.sh
```

## Docker Support

Build and run using Docker:
```bash
make dcr
```

## Project Structure

```
.
├── emsal_scraper-dev/    # Web scraping components
├── src/                  # Main source code
├── sample_data/          # Sample JSON documents
├── docs/                 # Scraped documents (gitignored)
├── md_docs/             # Processed markdown files (gitignored)
└── requirements.txt      # Python dependencies
```

## Features

- Anonymous web scraping with IP rotation
- Distributed document processing
- Keyword extraction with Turkish language support
- Vector similarity search
- Law reference extraction
- Progress monitoring and error handling
- Docker containerization

## Contributing

1. Fork the repository
2. Create your feature branch
3. Commit your changes
4. Push to the branch
5. Create a new Pull Request


## Acknowledgments

- EMSAL UYAP system
- Apache Spark and Spark NLP
- Milvus vector database
- Ollama project
