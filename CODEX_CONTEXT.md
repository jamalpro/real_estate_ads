# Codex Context: Real Estate Ads Dashboard

## Project purpose

This repository powers a static, browser-only dashboard for Syrian real estate WhatsApp ads. The app is meant to help browse, search, filter, compare, and triage real estate opportunities collected from WhatsApp groups and manual dumps.

Primary user goal: quickly find good investment opportunities in Syrian real estate ads, especially by area, price, property type, transaction type, size, and free-text criteria.

The project should remain simple, portable, and static. It should work when hosted on GitHub Pages and should not require a backend.

## Actual current workflow

The current operating workflow is **ChatGPT-assisted ingestion**:

1. The user copies one ad or multiple ads from WhatsApp.
2. The user pastes the raw ad text into this ChatGPT conversation.
3. ChatGPT parses every ad into structured JSON records.
4. ChatGPT appends those records to the repo data, extracting key facts:
   - area / neighborhood
   - price
   - currency
   - transaction type: sale, rent, wanted purchase, etc.
   - property type: residential, commercial, land, warehouse, office, etc.
   - size
   - floor / physical position
   - photos/video indicator
   - tags such as `طابو أخضر`, `سطح`, `حديقة`, `مدخل مستقل`, `تجاري`
   - derived fields such as `price_usd`, `price_per_m2`, `score`, `dedupe_key`
5. ChatGPT pushes the updated JSON/page files to GitHub.
6. GitHub Pages serves the updated static dashboard.

This means the parser must be durable and reusable across past and future ads. Do not treat parser fixes as one-off UI corrections only.

## Current repository structure

- `real_estate_ads.json`
  - Main ad database.
  - Contains `metadata` and an `ads` array.
  - The long-term goal is to append parsed ChatGPT records here directly and keep it authoritative.
  - Do not overwrite this large file from a stale local copy.

- `append_ads.py`
  - Durable WhatsApp-ad parser and append workflow.
  - Implements the parsing contract ChatGPT should follow when the user pastes raw WhatsApp ads.
  - It parses Arabic WhatsApp text, dedupes, appends to `real_estate_ads.json`, and can run `build.py`.
  - Keep this script aligned with the ChatGPT workflow.

- `manual_ads.json`
  - Temporary/small append layer for manually added records when editing the main JSON is risky.
  - Prefer direct append to `real_estate_ads.json` once the parser workflow is stable.

- `data_corrections.json`
  - Correction layer for known parser misses.
  - Use this to patch already-generated records when rewriting the main database is risky.
  - Long-term, fold corrections back into the parser and regenerated database.

- `index.html`
  - Current GitHub Pages entrypoint and polished static dashboard.
  - Loads `real_estate_ads.json`, `manual_ads.json`, and `data_corrections.json`.
  - Applies client-side repairs for missing price, area, and size from `raw_text`.
  - Supports favorites using localStorage with cookie fallback.

- `build.py`, `page.template.html`, `real_estate_ads.html`, `real_estate_ads.csv`
  - Earlier generated-dashboard workflow. Keep it available, but avoid regressing the newer `index.html` entrypoint.

- `smoke_test.js`
  - Node-based smoke test for the older generated HTML. Add/update tests for `index.html` when possible.

## Permanent parser rules

### Arabic thousand prices

Do not miss prices written as Arabic prose, especially:

- `100 الف`
- `100 ألف`
- `400 الف منهي`
- `المطلوب 250 الف`
- `100 الف وبازار`

For sale ads, these should normally parse as thousands of USD unless context clearly says otherwise:

- `100 الف` -> `100000`
- `400 الف` -> `400000`

Example bug fixed on 2026-09-01:

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

Rule: if a sale ad has no `price_usd`, or a suspiciously tiny sale price under `$5,000`, scan `raw_text` for `عدد + الف/ألف/الاف` and multiply by 1,000.

### Rent price versus wanted-buy language

Do not misclassify rent ads because of the word `مطلوب`.

Example:

```text
للإيجار محل
... 
مطلوب 400 دولار
```

This means asking rent, not `مطلوب شراء`.

Priority rule:

1. If the ad begins with or clearly contains `للإيجار`, `للاجار`, `للايجار`, `ايجار`, classify as `إيجار`.
2. Only classify as `مطلوب شراء` if the phrase explicitly says `مطلوب شراء` or clearly asks to buy.
3. `مطلوب 400 دولار` by itself is an asking price.

### Area/neighborhood inference

If `area` or `area_group` is missing, scan `raw_text` for known neighborhood names and variants. Examples:

- `الميسات عند دوار الميسات` -> `الميسات`
- `قبل جامع ابو النور` -> usually `الميسات`
- `شعلان` -> `الشعلان`
- `جسر الأبيض` / `الجسر الأبيض` -> `الجسر الأبيض`
- `أبو رمانة` / `ابو رمانة` -> `أبو رمانة`
- `مزة` / `المزة` -> `المزة`

Keep raw text visible because inferred neighborhoods may need human verification.

### Size extraction

Recognize size patterns such as:

- `80م`
- `80 م`
- `80 متر`
- `مساحة 300 متر`
- `المساحة 105م`

Do not confuse price thousands with square meters. Prefer size values near `مساحة`, `متر`, `م2`, or `م`.

### Derived fields

After parsing, always compute or update:

- `price_usd`
- `currency_norm`
- `price_per_m2` for sale ads where price and size are known
- `dedupe_key`
- `score`
- `has_photos`
- normalized `area_group`, `category_group`, `transaction_group`

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

The app supports Arabic text and Arabic-Indic digits. Keep Arabic normalization behavior working when modifying search or parsing.

## Build and test commands

For durable ingestion from a pasted file:

```bash
python3 append_ads.py pasted_ads.txt
```

This appends parsed ads to `real_estate_ads.json` and runs `build.py` unless `--no-build` is passed.

Generated-dashboard flow:

```bash
python3 build.py
node smoke_test.js
```

For the current `index.html` dashboard, add a direct browser or Node/jsdom style test when possible. The page includes browser-console self-tests for loaded ad count, repair counts, favorite count, and map-marker count.

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
4. For new pasted WhatsApp ads, parse with `append_ads.py` rules and append structured records.
5. Prefer direct fixes to the durable parser over one-off corrections.
6. Use `data_corrections.json` only as a safety layer for already-published bad records.
7. Run available tests or add browser-console self-tests for static UI logic.
8. Summarize changed files and testing results.
9. Call out any assumptions or known limitations.
