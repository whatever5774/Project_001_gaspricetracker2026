# Costco Gas Price Tracker

A Python-based automated solution to fetch official daily gas prices from specific Costco warehouses, bypass bot-detection using Playwright Stealth, and send alerts directly via Twilio SMS.

## Why this project?
Costco does not provide an official API for its gas prices, and its website employs strict anti-scraping measures. This tool uses `playwright` with stealth plugins to mimic human browsing behavior to extract gas prices from the warehouse pages directly. 

## Directory Structure
- `src/` - Core execution scripts (`main.py`, `scraper.py`, `notifier.py`)
- `tests/` - Standalone scripts used to test/debug various logic (SMS sending, UI interactions, GraphQL requests)
- `debug_data/` - Temporary files, error screenshots, and HTML dumps generated during fetching and debugging (Excluded from git).

## Setup
### 1. Requirements
Ensure you have Python 3.10+ installed. Install the dependencies and the necessary browser binaries:
```bash
pip install -r src/requirements.txt
playwright install chromium
```

### 2. Environment Variables (.env)
Create a `.env` file in the root of the project (you can copy from `.env.example`) and fill in your Twilio credentials:
```env
TWILIO_ACCOUNT_SID=your_account_sid
TWILIO_AUTH_TOKEN=your_auth_token
TWILIO_FROM_NUMBER=+1234567890
TO_PHONE_NUMBER=+1987654321
ZIP_CODE=91709  # Optional if logic uses zipcode
```

## Running the tool Locally
To run the scraper and trigger the SMS alert manually on your local machine:
```bash
cd src
python main.py
```

## Automated GitHub Actions
The tool is set up to run automatically every day using GitHub Actions (see `.github/workflows/daily_alert.yml`). 
To ensure it runs successfully, add the environment variables defined in `.env` as Repository Secrets (`Settings` -> `Secrets and variables` -> `Actions`) in your GitHub repository.
