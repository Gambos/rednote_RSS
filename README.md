# xhsRSS Scraper

This repository contains scripts for scraping content from XiaoHongShu (小红书).

## Files

- `xhs_scraper.py` - core scraping logic
- `xhs_scraper_public.py` - public-facing entrypoint
- `xhs_session.json` - session data

## Setup

1. Create a virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate  # or venv\Scripts\activate on Windows
   ```
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

## Usage

1. **Login** (only needed once):
   ```bash
   python xhs_scraper.py --login
   ```
   This will open a real browser window. Scan the QR code to log in to XiaoHongShu, then press Enter in the terminal once you have finished. Your session state will be saved to `xhs_session.json`.

2. **Scrape**:
   ```bash
   python xhs_scraper.py
   ```
   The results will be printed to the terminal and also saved to `xhs_digest.txt`.

(You can also run `xhs_scraper_public.py` — it's just a thin command‑line wrapper and uses the same underlying logic as `xhs_scraper.py`.)
