# Codex Context: Real Estate Ads Dashboard

## Project purpose

This repository powers a static, browser-only dashboard for Syrian real estate WhatsApp ads. The app is meant to help browse, search, filter, compare, and triage real estate opportunities collected from WhatsApp groups and manual dumps.

Primary user goal: quickly find good investment opportunities in Syrian real estate ads, especially by area, price, property type, transaction type, size, and free-text criteria.

The project should remain simple, portable, and static. It should work from a local file opened directly in a browser and should also work when hosted on GitHub Pages.

## Current repository structure

- `real_estate_ads.json`
  - Source of truth for all ad records.
  - Contains `metadata` and an `ads` array.
  - Do not manually edit generated fields unless necessary; prefer changing source values and running `build.py`.

- `build.py`
  - Regenerates derived fields, validates records, writes `real_estate_ads.csv`, and generates `real_estate_ads.html` from `page.template.html`.
  - Run this after editing `real_estate_ads.json` or `page.template.html`.
  - Important: `real_estate_ads.html` is generated output. Do not hand-edit it.

- `page.template.html`
  - Main UI template and client-side JavaScript.
  - This is the correct file to edit when improving the UI.
  - The template contains `{{ADS_JSON}}`; `build.py` replaces that placeholder with the full JSON payload.

- `real_estate_ads.html`
  - Generated standalone dashboard.
  - Can be opened directly in a browser.
  - Can be served by GitHub Pages.

- `real_estate_ads.csv`
  - Spreadsheet-friendly export generated from the JSON.

- `smoke_test.js`
  - Node-based smoke test for the generated HTML.
  - It checks that the dashboard renders, search works, Arabic normalization works, digit search works, price filter works, table mode works, and CSV export works.

- `append_ads.py`
  - Placeholder workflow helper. Current data appends are still handled outside this repo or by future parser work.

- `README.md`
  - Basic project description, publishing instructions, and update workflow.

## Data model notes

Common fields on each ad include:

- `id`
- `date`, `date_iso`, `stamp_raw`
- `transaction`, `transaction_group`
- `category`, `category_group`
- `area`, `area_group`
- `price`, `currency`, `currency_norm`, `price_usd`, `price_text`
- `size_m2`, `land_dunum`, `floor`, `price_per_m2`
- `score`
- `has_photos`
- `tags`
- `raw_text`
- `dedupe_key`

The app supports Arabic text and Arabic-Indic digits. Keep Arabic normalization behavior working when modifying search.

## Build and test commands

Run these from the repo root:

```bash
python3 build.py
node smoke_test.js
```

Expected result:

- `build.py` rewrites `real_estate_ads.json`, `real_estate_ads.csv`, and `real_estate_ads.html`.
- `smoke_test.js` should print an all-checks-passed message.

Before committing UI changes, run both commands.

## Product direction

This should feel like a polished real estate ads product, not a raw data dump.

Target experience:

- Fast search and filtering.
- Beautiful, readable listing cards.
- Clear investment-relevant facts: area, price, size, price per m², transaction type, property type, floor, score, tags, photos/video indicator.
- Good mobile layout.
- Useful summary stats.
- Clear empty states.
- Easy table mode for power users.
- Easy export of filtered results.

Arabic/RTL should remain first-class. Keep the document `lang="ar" dir="rtl"` unless there is a deliberate reason to change it.

## First task: improve the UI design

Improve `page.template.html` so the generated `real_estate_ads.html` looks like a modern, user-friendly real estate listings page.

### Goals

1. Make the dashboard visually polished and easier to scan.
2. Preserve all existing functionality:
   - search
   - filters
   - sorting
   - card/table toggle
   - CSV export
   - Arabic normalization
   - Arabic-Indic digit matching
   - dark-mode support if possible
3. Keep it static and dependency-free unless there is a strong reason not to.
4. Maintain GitHub Pages/local-file compatibility.
5. Keep `smoke_test.js` passing, updating tests only when UI markup changes make that necessary.

### Suggested UI improvements

- Add a richer hero/header area with:
  - page title
  - short subtitle explaining the dashboard
  - last updated date
  - total ad count
  - quick action buttons

- Improve filter layout:
  - make search more prominent
  - group filters into a clean panel
  - add clear labels, not only placeholders
  - make mobile layout cleaner

- Improve stats:
  - use visually distinct stat cards
  - show total filtered results, sale count, rent count, median price per m²
  - optionally add commercial/residential counts if available

- Improve listing cards:
  - stronger title hierarchy
  - clearer price block
  - show area/category/transaction as chips
  - show key facts in a compact grid
  - show score as a badge or meter
  - show tags cleanly
  - collapse or visually separate raw WhatsApp text

- Improve interaction affordances:
  - sticky filter bar should not consume too much vertical space on mobile
  - buttons should have clear states
  - table/card toggle should be obvious
  - empty state should tell the user how to recover

- Improve visual style:
  - use a warmer real-estate-style palette
  - add better spacing and shadows
  - improve typography and line-height for Arabic text
  - use responsive cards with comfortable min/max widths

### Constraints

- Do not hand-edit `real_estate_ads.html`; it is generated.
- Edit `page.template.html` and then run `python3 build.py`.
- Keep the data island script: `<script id="ads-data" type="application/json">{{ADS_JSON}}</script>`.
- Avoid external CDNs so the page remains portable and works offline.
- Do not remove raw ad text; it is important for verification.
- Do not remove table mode or CSV export.
- Preserve accessibility basics: labels, readable contrast, keyboard-friendly controls.

## Future likely tasks

- Build a real parser for appending WhatsApp dumps directly from text files.
- Add saved presets for target areas and investment criteria.
- Add stronger deduplication and record merge workflow.
- Add edit/review flags for suspicious price parsing.
- Add map/location enrichment when exact addresses become available.
- Add analytics: price per m² by area, top opportunities, investment scoring explanation.
- Add GitHub Actions to run `python3 build.py` and `node smoke_test.js` on pull requests.

## User/project preferences

The user is monitoring Syrian real estate ads, with recurring interest in areas such as:

- أبو رمانة
- المالكي
- الروضة
- ماروتا
- المزرعة
- برنية / برينية
- شارع بغداد
- الجسر الأبيض
- الشهبندر
- الميسات
- العدوي
- المهاجرين
- ركن الدين / شرقي ركن الدين

Earlier investment criteria included ground-floor properties, storage/basement, mixed residential-commercial usability, independent entrances, green title deeds, commercial title/finance, and medical/business suitability. The user later broadened the goal from pharmacy-specific opportunities to general investment opportunities.

When improving UI, highlight information useful for investment triage, not only residential browsing.

## Working style for Codex/ChatGPT

When modifying this repo:

1. Inspect the current file before editing.
2. Make focused, reviewable changes.
3. Prefer editing source files over generated files.
4. Run build and smoke tests.
5. Summarize changed files and testing results.
6. Call out any assumptions or known limitations.
