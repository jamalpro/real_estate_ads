# Real Estate Ads Dashboard

Standalone local dashboard and data files for Syrian real estate WhatsApp ads.

## Files

- `real_estate_ads.html` - standalone searchable/filterable HTML dashboard. Open this directly in a browser.
- `real_estate_ads.json` - source database used by the dashboard.
- `real_estate_ads.csv` - spreadsheet-friendly export.

## Current data

The current dataset contains 206 ad records in `real_estate_ads.json`.

## Publish to GitHub Pages

After pushing this repo to GitHub, enable GitHub Pages:

1. Go to **Settings -> Pages**.
2. Source: **Deploy from a branch**.
3. Branch: `main` and folder `/root`.
4. Save.

The dashboard should then be available at:

`https://jamalpro.github.io/real_estate_ads/real_estate_ads.html`

## Update workflow

When new WhatsApp ads are added, update `real_estate_ads.json`, regenerate `real_estate_ads.csv` and `real_estate_ads.html`, then commit and push.
