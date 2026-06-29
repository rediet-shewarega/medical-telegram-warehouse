# Medical Telegram Data Warehouse

## Project Overview
This project scrapes Ethiopian medical-related Telegram channels, stores raw messages and images in a local data lake, loads the raw JSON data into PostgreSQL, and transforms it into a clean dimensional warehouse using dbt.

## Completed Tasks

### Task 1: Data Scraping and Collection
- Scraped Telegram channels:
  - CheMed
  - Lobelia Cosmetics
  - Tikvah Pharma
  - Hakimed Medical Resources
- Stored raw JSON files in:
  - `data/raw/telegram_messages/YYYY-MM-DD/channel_name.json`
- Downloaded images into:
  - `data/raw/images/channel_name/message_id.jpg`
- Implemented logging in:
  - `logs/scraper.log`

Local scraping summary:
- Total JSON files: 7
- Total messages scraped: 652
- Total downloaded images: 269

### Task 2: Data Modeling and Transformation
- Loaded raw JSON data into PostgreSQL table:
  - `raw.telegram_messages`
- Built dbt staging model:
  - `stg_telegram_messages`
- Built dimensional mart models:
  - `dim_channels`
  - `dim_dates`
  - `fct_messages`
- Implemented dbt tests and custom tests.
- Generated and served dbt documentation.

## dbt Test Result
`dbt test` completed successfully:

- PASS = 24
- WARN = 0
- ERROR = 0
- TOTAL = 24

## How to Run

Start PostgreSQL:

```bash
docker compose up -d