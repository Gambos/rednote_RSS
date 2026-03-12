# xhsRSS Scraper

This repository contains scripts for fetching posts from the last 24 hours matching custom keywords on Rednote/XiaoHongShu, delivering a daily digest.

## Files

- `xhs_scraper_public.py` – the public template script with core scraping logic and command‑line options; you can edit the configuration lists at the top to set your keywords, categories, and filters.
- `xhs_scraper_example.py` – an example showing how you might customize keywords or tweak behavior for a different use case.
- `xhs_session.json` – stores the browser login/session state after the first login.
- `xhs_seen.json` – (created during scraping) keeps track of already‑seen post IDs to avoid duplicates; it is not included in the repo.

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

### Customizing keywords and filters

If you use `xhs_scraper_public.py` directly, you can edit the top of that file to adjust the following lists to suit your needs:

- `KEYWORDS` – the search terms used for scraping.
- `NOISE_KEYWORDS` – substrings whose presence in a title will cause the post to be ignored.
- `BLOGGERS` – an optional list of specific bloggers to track (each entry is a `{"name": ..., "id": ...}` object).

Feel free to modify these arrays and re‑run the script; they are plain Python lists at the top of the file.
