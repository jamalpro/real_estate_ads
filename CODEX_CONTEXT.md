# Codex Context: Real Estate Ads Dashboard

## Project purpose

This repository powers a static, browser-only dashboard for Syrian real estate WhatsApp ads. The app is meant to help browse, search, filter, compare, and triage real estate opportunities collected from WhatsApp groups and manual dumps.

Primary user goal: quickly find good investment opportunities in Syrian real estate ads, especially by area, price, property type, transaction type, size, and free-text criteria.

The project should remain simple, portable, and static. It should work from a local file opened directly in a browser and should also work when hosted on GitHub Pages.

## Current repository structure

- `real_estate_ads.json`
  - Generated/source database for the main ad records.
  - Contains `metadata` and an `ads` array.
  - Do not casually overwrite this large file from an old local copy.

- `manual_ads.json`
  - Small append-only layer for ads added manually from the ChatGPT conversation.
  - The live `index.html` merges this with `real_estate_ads.json` at load time.

- `data_corrections.json`
  - Small correction layer for known parser misses.
  - Use this when one or a few generated records need fixes but regenerating the full database is risky.
  - Corrections are keyed by `id` or `dedupe_key` and applied by `index.html` after loading data.

- `index.html`
  - Current GitHub Pages entrypoint and polished static dashboard.
  - Loads `real_estate_ads.json`, `manual_ads.json`, and `data_corrections.json`.
  - Applies client-side repairs for missing price, area, and size from `raw_text`.
  - Supports favorites using localStorage with a cookie fallback.

- `build.py`, `page.template.html`, `real_estate_ads.html`, `real_estate_ads.csv`
  - Earlier generated-dashboard workflow. Keep it available, but be careful not to regress the newer `index.html` entrypoint.

- `smoke_test.js`
  - Node-based smoke test for the generated HTML. If the main dashboard remains `index.html`, add/update tests for `index.html` too.

## Critical parser lessons

### Arabic thousand prices

Do not miss prices written as Arabic prose, especially:

- `100 الف`
- `100 ألف`
- `400 الف منهي`
- `المطلوب 250 الف`

For sale ads, these should normally parse as thousands of USD unless context clearly says otherwise:

- `100 الف` -> `100000`
- `400 الف` -> `400000`

Example bug fixed on 2026-09-01:

Raw text:

```text
🌷شقه للبيع الميسات عند دوار الميسات
نزول شاحطين مشمس ومهوي 80م غرفتين وصالون وجنينه اكساء سوبر ديلوكس لسا ما انسكن البيت 
الملكية حكم محكمه قابل يصيرطابو
100 الف وبازار.🌷.
```

Correct parse:

- transaction: `بيع`
- area: `الميسات`
- price: `100000`
- currency_norm: `USD`
- size_m2: `80`
- price_per_m2: `1250`

Rule: if a sale ad has no `price_usd`, or a suspiciously tiny sale price under `$5,000`, scan `raw_text` for `عدد + الف/ألف/الاف` and multiply by 1,000. Do not treat `مطلوب 400 دولار` in a rental ad as buyer demand; it may mean asking rent.

### Area/neighborhood inference

If `area` or `area_group` is missing, scan `raw_text` for known neighborhood names and variants. Examples:

- `الميسات عند دوار الميسات` -> `الميسات`
- `قبل جامع ابو النور` -> usually `الميسات`
- `شعلان` -> `الشعلان`
- `جسر الأبيض` / `الجسر الأبيض` -> `الجسر الأبيض`
- `أبو رمانة` / `ابو رمانة` -> `أبو رمانة`
- `مزة` / `المزة` -> `المزة`

Keep raw text visible because inferred neighborhoods need human verification.

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

Run these from the repo root when using the generated-dashboard flow:

```bash
python3 build.py
node smoke_test.js
```

For the current `index.html` dashboard, add a direct browser or Node/jsdom style test when possible. The page currently includes a browser-console self-test that logs loaded ad count, repair counts, favorite count, and map-marker count.

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
- Local favorites stored on device only.
- A simple neighborhood map/marker panel that helps browse by area.

Arabic/RTL should remain first-class. Keep the document `lang="ar" dir="rtl"` unless there is a deliberate reason to change it.

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
3. Do not overwrite large generated files from stale local copies.
4. Prefer correction/append layers when full regeneration is risky.
5. Run available tests or add browser-console self-tests for static UI logic.
6. Summarize changed files and testing results.
7. Call out any assumptions or known limitations.
