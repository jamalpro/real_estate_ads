# Codex Context: Real Estate Ads Dashboard

## Project purpose

This repository powers a static, browser-only dashboard for Syrian real estate WhatsApp ads. The app is meant to help browse, search, filter, compare, and triage real estate opportunities collected from WhatsApp groups and manual dumps.

Primary user goal: quickly find good investment opportunities in Syrian real estate ads, especially by area, price, property type, transaction type, size, and free-text criteria.

The project should remain simple, portable, and static. It should work when hosted on GitHub Pages and should not require a backend.

## Non-negotiable ingestion authority

Read `LLM_INGESTION_RULES.md` before ingesting any new ads.

The authority chain is:

1. **Images/videos are read by ChatGPT LLM vision.** Frame extraction/contact sheets may be mechanical, but traditional OCR is only a hint and must not be used as the final source of truth.
2. **Raw text is parsed by ChatGPT LLM.** Python, regex, and scripts are not the semantic parser of record.
3. **Deduplication is decided by ChatGPT LLM.** Deterministic keys are hints only; duplicate decisions must compare meaning, location, price, size, floor, and raw phrasing.
4. **Neighborhood and price knowledge is learned from the text corpus.** Area spellings, landmarks, and price formats are non-standard and must be maintained as evolving LLM context/rules.

Scripts may store, merge, validate, compute simple derived arithmetic, and rebuild static files. Scripts must not be treated as the authority for OCR, semantic parsing, neighborhood interpretation, price interpretation, or ambiguous dedupe.

## Actual current workflow

The current operating workflow is **ChatGPT/LLM-assisted ingestion**.

The LLM in the ChatGPT conversation is the parser of record for new pasted WhatsApp ads. Repository scripts may validate, normalize, dedupe hints, or rebuild files, but they must not be treated as the primary source of interpretation when the user pastes raw ads into chat.

Workflow for pasted text:

1. The user copies one ad or multiple ads from WhatsApp.
2. The user pastes the raw ad text into this ChatGPT conversation.
3. ChatGPT LLM reads the raw Arabic text and separates ads when needed.
4. ChatGPT LLM parses every ad into structured JSON records.
5. ChatGPT LLM performs semantic dedupe against known/suspected existing records.
6. ChatGPT appends only LLM-approved structured records to the repo data.
7. GitHub Pages serves the updated static dashboard.

Workflow for screenshots/videos:

1. Extract frames/contact sheets only as visual evidence.
2. ChatGPT LLM vision reads visible ad text from the frames.
3. ChatGPT LLM reconstructs complete ads from repeated/partial frames.
4. ChatGPT LLM parses and semantically dedupes the reconstructed ads.
5. Only LLM-reviewed records may be written to GitHub.

Important: do not tell the user that parsing must happen by a deterministic script first. The intended workflow is that ChatGPT does the semantic parsing here in chat, then writes the structured result to the repository.

## Role of scripts

- `append_ads.py` is a helper/reference validator for parser rules, not the authority over pasted ad interpretation.
- `merge_manual_ads.py` is only a storage/merge helper for ChatGPT-approved records.
- Scripts may normalize fields, compute derived values, validate structure, or rebuild files after the LLM creates structured records.
- If a script disagrees with the LLM on a semantic point, inspect the raw text/image in ChatGPT and resolve it there before writing final JSON.
- Do not add scripts that stage OCR-derived records automatically.

## Current repository structure

- `real_estate_ads.json`
  - Main ad database.
  - Contains `metadata` and an `ads` array.
  - The long-term goal is to append parsed ChatGPT records here directly and keep it authoritative.
  - Do not overwrite this large file from a stale local copy.

- `LLM_INGESTION_RULES.md`
  - Permanent source-of-truth rules for LLM vision OCR, text parsing, semantic dedupe, neighborhood learning, and price learning.
  - Read this before adding ads from pasted text, screenshots, or video.

- `append_ads.py`
  - Helper/reference parser and validation workflow.
  - Mirrors some parsing contract checks ChatGPT should follow, but it should not replace ChatGPT LLM semantic parsing.

- `manual_ads.json`
  - Temporary/small append layer for LLM-approved ChatGPT-parsed records when editing the main JSON is risky.
  - It should be merged into `real_estate_ads.json` and removed by the workflow.

- `data_corrections.json`
  - Correction layer for known parser misses.
  - Use this to patch already-generated records when rewriting the main database is risky.
  - Long-term, fold corrections back into LLM rules and regenerated database.

- `index.html`
  - Current GitHub Pages entrypoint and polished static dashboard.
  - Loads `real_estate_ads.json` and optional correction/temporary layers.
  - Supports favorites using localStorage with cookie fallback.

- `build.py`, `page.template.html`, `real_estate_ads.html`, `real_estate_ads.csv`
  - Earlier generated-dashboard workflow. Keep it available, but avoid regressing the newer `index.html` entrypoint.

- `smoke_test.js`
  - Node-based smoke test for the older generated HTML. Add/update tests for `index.html` when possible.

## Permanent LLM parser rules

These rules are for ChatGPT LLM parsing first, and script validation second.

### Arabic thousand prices

Do not miss prices written as Arabic prose, especially:

- `100 الف`
- `100 ألف`
- `400 الف منهي`
- `المطلوب 250 الف`
- `100 الف وبازار`
- `400الف $`
- `575 الف$ وبازار`

For sale ads, these should normally parse as thousands of USD unless context clearly says otherwise:

- `100 الف` -> `100000`
- `400 الف` -> `400000`
- `575 الف` -> `575000`

Rule: if a sale ad has no `price_usd`, or a suspiciously tiny sale price under `$5,000`, the LLM must re-read the full raw text for `عدد + الف/ألف/الاف` and infer thousands from context.

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

### Area/neighborhood learning

If `area` or `area_group` is missing or ambiguous, the LLM should inspect full raw text, landmarks, and spelling variants. Examples:

- `شرقي ركن الدين`, `بشرقي ركن الدين`, `ركن الدين شرقي` -> likely `ركن الدين`, subarea `شرقي ركن الدين`
- `الميسات عند دوار الميسات` -> `الميسات`
- `قبل جامع ابو النور` -> usually `الميسات`
- `تنظيم كفرسوسة`, `تنظيم كفرسوسة شارع لافيولا` -> `كفرسوسة`, subarea `تنظيم كفرسوسة`
- `شعلان` -> `الشعلان`
- `جسر الأبيض` / `الجسر الأبيض` -> `الجسر الأبيض`
- `أبو رمانة` / `ابو رمانة` -> `أبو رمانة`
- `مزة` / `المزة` / `مزه` -> `المزة`
- `العدوي الفيلااات`, `العدوي الفيلات` -> `العدوي`, subarea `الفيلات`

Capture landmarks as tags when useful: `جسر الحياة`, `جامع الإيمان`, `مرشد خاطر`, `مدرسة أنور العطار`, `الهجرة والجوازات`, `لافيولا`, `ماروتا سيتي`, `جبل قاسيون`.

Keep raw text visible because inferred neighborhoods may need human verification.

### Size extraction

Recognize size patterns such as:

- `80م`
- `80 م`
- `80 متر`
- `مساحة 300 متر`
- `المساحة 105م`
- `مساحة 200م²`

Do not confuse price thousands with square meters. Prefer size values near `مساحة`, `متر`, `م2`, `م²`, or `م`.

### LLM semantic dedupe

Generated IDs are not dedupe evidence. Deterministic dedupe keys are hints only.

Two records may be duplicates when several of these match:

- same neighborhood/subarea or landmark
- same size
- same price
- same floor
- same room count
- same deed/title details
- same unusual phrases or features
- repeated frames from the same WhatsApp screen recording

If uncertain, do not silently drop the record. Mark `needs_review: true` or keep both with a note explaining why.

### Derived fields

After parsing, always compute or update:

- `price_usd`
- `currency_norm`
- `price_per_m2` for sale ads where price and size are known
- `dedupe_key` as a hint, not authority
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
- `needs_review`, `review_reason`, `llm_reading_confidence` when confidence is imperfect

The app supports Arabic text and Arabic-Indic digits. Keep Arabic normalization behavior working when modifying search or parsing.

## Build and test commands

For the current ChatGPT workflow, first parse in chat, then write JSON. Scripts are optional checks.

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
4. For new pasted WhatsApp ads, ChatGPT LLM parses the raw text here in chat first.
5. For screenshots/videos, ChatGPT LLM vision reads the frames here in chat first.
6. ChatGPT LLM decides semantic dedupe; scripts only provide hints.
7. Scripts may validate or normalize the LLM-parsed structured record, but should not override the semantic parse without checking the raw text/image.
8. Prefer durable LLM-context/rule updates over one-off corrections.
9. Use `data_corrections.json` only as a safety layer for already-published bad records.
10. Run available tests or add browser-console self-tests for static UI logic.
11. Summarize changed files and testing results.
12. Call out any assumptions or known limitations.
