# Costco Gas Price Tracker

A Python-based automated solution to fetch official daily gas prices from specific Costco warehouses, bypass bot-detection using Playwright Stealth, and send alerts via Twilio SMS **only when prices change**.

## Features

- 🛡️ **Anti-bot bypass** — Uses Playwright + stealth plugin to mimic human browsing
- 📡 **API-based scraping** — Calls the internal `AjaxGetGasPricesService` API directly for reliable JSON data
- 💰 **Smart alerts** — Only sends SMS when Regular gas price changes by **≥ $0.05** at Ontario or Eastvale
- 📊 **Price history** — Records every scrape to `docs/price_history.csv` for trend analysis
- 📈 **Dashboard** — Interactive Chart.js price trend dashboard hosted via **GitHub Pages**
- 📧 **Weekly report** — Email summary every Friday morning via Gmail SMTP
- ⚡ **Twice-daily checks** — Runs at 8:00 AM and 8:00 PM Pacific Time via GitHub Actions

## How It Works

```
┌─────────────┐    ┌──────────────┐    ┌───────────────┐
│  Playwright  │───▶│  Price Store │───▶│  Conditional  │
│  Scraper     │    │  (compare)   │    │  SMS / Email  │
└─────────────┘    └──────────────┘    └───────────────┘
                          │
                          ▼
                   ┌──────────────┐
                   │  CSV History │───▶ GitHub Pages Dashboard
                   └──────────────┘
```

- **First run**: Records baseline prices, does NOT send SMS
- **Subsequent runs**: Compares current vs cached Regular prices for Ontario & Eastvale
- **Price change ≥ $0.05**: Sends SMS with old → new comparison
- **No change**: Logs "价格未变" (price unchanged), skips SMS
- **Friday 8 AM**: Sends weekly email report with all 3 stores' current prices

## Directory Structure

```
├── src/
│   ├── main.py              # Main entry point
│   ├── scraper.py           # Playwright scraper (AjaxGetGasPricesService API)
│   ├── notifier.py          # Twilio SMS + Gmail email sender
│   ├── config.py            # Environment variable configuration
│   ├── price_store.py       # Price cache, comparison, and CSV history
│   └── requirements.txt     # Python dependencies
├── docs/
│   ├── index.html           # Chart.js price trend dashboard
│   └── price_history.csv    # Historical price data (auto-appended)
├── .github/workflows/
│   ├── daily_alert.yml      # Twice-daily price check + SMS alert
│   └── weekly_report.yml    # Friday weekly email report
└── tests/                   # Debug and test scripts
```

## Setup

### 1. Requirements

Ensure you have Python 3.10+ installed. Install the dependencies and browser binaries:

```bash
pip install -r src/requirements.txt
playwright install chromium
```

### 2. Environment Variables (.env)

Create a `.env` file in the project root (copy from `.env.example`) and fill in your credentials:

```env
# Twilio SMS
TWILIO_ACCOUNT_SID=your_account_sid
TWILIO_AUTH_TOKEN=your_auth_token
TWILIO_FROM_NUMBER=+1234567890
TO_PHONE_NUMBER=+1987654321

# Gmail SMTP (for weekly report)
GMAIL_ADDRESS=your_email@gmail.com
GMAIL_APP_PASSWORD=your_16_char_app_password
REPORT_TO_EMAIL=recipient@example.com

# Optional: Override target URLs
# COSTCO_TARGET_URLS=https://www.costco.com/w/-/ca/chino%20hills/473,...
```

> **Gmail App Password**: Enable 2FA on your Google account, then generate an App Password at [myaccount.google.com/apppasswords](https://myaccount.google.com/apppasswords).

### 3. GitHub Secrets

Add these secrets in your repository (`Settings` → `Secrets and variables` → `Actions`):

| Secret | Description |
|--------|-------------|
| `TWILIO_ACCOUNT_SID` | Twilio Account SID |
| `TWILIO_AUTH_TOKEN` | Twilio Auth Token |
| `TWILIO_FROM_NUMBER` | Twilio sender phone number |
| `TO_PHONE_NUMBER` | Recipient phone number |
| `GMAIL_ADDRESS` | Gmail address for weekly report |
| `GMAIL_APP_PASSWORD` | Gmail App Password |
| `REPORT_TO_EMAIL` | Recipient email for weekly report |

### 4. GitHub Pages (Dashboard)

Enable GitHub Pages in your repository settings:
- **Source**: Deploy from a branch → `main` → `/docs` folder
- Dashboard will be available at `https://<your-username>.github.io/<repo-name>/`

## Running Locally

### Normal price check (with SMS if changed):
```bash
cd src
python main.py
```

### Weekly report email:
```bash
cd src
python main.py --weekly-report
```

### Testing price change detection:

1. First run creates baseline:
   ```bash
   cd src && python main.py
   # → "首次运行 — 保存当前价格为基线，不发送短信。"
   ```

2. Second run (no real change):
   ```bash
   cd src && python main.py
   # → "价格未变，不发送短信。"
   ```

3. Manually edit `src/prices_cache.json` to simulate a change, then re-run:
   ```bash
   cd src && python main.py
   # → Sends SMS with old → new comparison
   ```

## SMS Format

When prices change, the SMS looks like:

```
Costco Gas Price Change:
1. Ontario Bus Ctr Ontario: $4.59 → $4.69 (+$0.10)
2. Eastvale: $4.55 → $4.60 (+$0.05)
```

## Configuration Reference

| Config | Default | Description |
|--------|---------|-------------|
| `PRICE_CHANGE_THRESHOLD` | `0.05` | Minimum Regular price change to trigger SMS |
| `ALERT_CITIES` | `["Ontario Bus Ctr Ontario", "Eastvale"]` | Cities that trigger SMS alerts |
| `PRICE_CACHE_FILE` | `prices_cache.json` | Path to price cache |
| `PRICE_HISTORY_FILE` | `../docs/price_history.csv` | Path to history CSV |

## Automated GitHub Actions

### Daily Price Monitor (`daily_alert.yml`)
- Runs **twice daily**: 8:00 AM and 8:00 PM Pacific Time
- Checks prices for all 3 Costco warehouses
- Sends SMS only if Ontario or Eastvale Regular price changes ≥ $0.05
- Updates `docs/price_history.csv` automatically

### Weekly Report (`weekly_report.yml`)
- Runs **every Friday at 8:00 AM** Pacific Time
- Sends email with all 3 stores' current prices via Gmail SMTP

Both workflows can also be triggered manually via the Actions tab (`workflow_dispatch`).
