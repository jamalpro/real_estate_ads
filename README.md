# Real Estate Ads Dashboard

Standalone local dashboard and data files for Syrian real estate WhatsApp ads.

## Files

- `index.html` - GitHub Pages root entry point for the dashboard.
- `real_estate_ads.html` - standalone searchable/filterable HTML dashboard. Open this directly in a browser.
- `real_estate_ads.json` - source database used by the dashboard.
- `real_estate_ads.csv` - spreadsheet-friendly export.
- `page.template.html` - dashboard template. Edit this for UI changes, then run `python3 build.py`.
- `build.py` - regenerates derived files from the JSON and template.
- `smoke_test.js` - lightweight regression test for rendering, search, filters, sorting, table mode, and CSV export.

## Current data

The current dataset contains 206 ad records in `real_estate_ads.json`.

## Publish to GitHub Pages

After pushing this repo to GitHub, enable GitHub Pages:

1. Go to **Settings -> Pages**.
2. Source: **Deploy from a branch**.
3. Branch: `main` and folder `/root`.
4. Save.

The dashboard should then be available at:

`https://jamalpro.github.io/real_estate_ads/`

The explicit generated file URL also works:

`https://jamalpro.github.io/real_estate_ads/real_estate_ads.html`

## Update workflow

When new WhatsApp ads are added, update `real_estate_ads.json`, then run:

```bash
python3 build.py
node smoke_test.js
```

Commit and push the changed `real_estate_ads.json`, `real_estate_ads.csv`, `real_estate_ads.html`, and `index.html` files.
