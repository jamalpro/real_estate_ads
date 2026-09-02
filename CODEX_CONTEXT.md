# Codex Context: Real Estate Ads Dashboard

## Project purpose

This repository powers a static, browser-only dashboard for Syrian real estate WhatsApp ads. The app helps browse, search, filter, compare, and triage real estate opportunities collected from WhatsApp groups and manual dumps.

Primary user goal: quickly identify useful Syrian real estate investment opportunities by area, price, property type, transaction type, size, price per square meter, and free-text criteria.

The project should remain simple, portable, and static. It should work on GitHub Pages and should not require a backend.

## Current source of truth

`real_estate_ads.json` is the single source of truth for published ad data.

`manual_ads.json` may be used only as a temporary small staging layer for ChatGPT-approved structured records when editing the large main JSON directly is risky. After a successful merge, it should be deleted.

Do not reintroduce separate correction, CSV, or deterministic-parser layers unless the user explicitly asks. Git history is the backup and rollback mechanism.

## Non-negotiable ingestion authority

This project uses ChatGPT / LLM judgment as the authority for reading and interpreting Syrian real estate ads.

1. **Images and videos must be read with ChatGPT LLM vision.**
   - Frame extraction/contact sheets may be mechanical.
   - Traditional OCR output may be used only as a rough hint.
   - The final readable text must be verified by ChatGPT vision/LLM from image frames.
   - Do not add records to the database from unreviewed OCR text.

2. **Raw pasted text must be parsed by ChatGPT LLM.**
   - Python scripts, regex, or deterministic parsers are not the semantic authority.
   - Scripts may only help with formatting, storage, field validation, JSON merging, obvious arithmetic, and static-site rebuilding.
   - If a script disagrees with the LLM interpretation, inspect the raw ad in ChatGPT and resolve it there.

3. **Deduplication must be decided by ChatGPT LLM.**
   - Deterministic dedupe keys are hints only.
   - The LLM must compare meaningful ad content: neighborhood, landmarks, size, price, floor, features, deed/title details, and raw phrasing.
   - Do not discard an ad solely because a script says it is similar.
   - Do not add an ad solely because a generated ID is different.

4. **Neighborhood and price knowledge must be learned from the corpus.**
   - Syrian WhatsApp ads use inconsistent spellings, shorthand, local landmarks, typo-heavy text, and mixed Arabic/English symbols.
   - Treat this as evolving LLM context, not a fixed regex problem.
   - When a new spelling, landmark, or price pattern appears, update this file.

## Current ingestion workflow

For pasted text:

1. User pastes one or more raw WhatsApp ads into ChatGPT.
2. ChatGPT LLM reads and separates the ads.
3. ChatGPT LLM parses each ad into structured fields.
4. ChatGPT LLM performs semantic dedupe against known or suspected existing ads.
5. ChatGPT writes only approved structured records to GitHub.
6. Repo scripts may merge approved records into `real_estate_ads.json` and rebuild the static dashboard.

For screenshots/videos:

1. Extract frames or contact sheets only as visual evidence.
2. ChatGPT LLM vision reads visible ad text from the frames.
3. ChatGPT LLM reconstructs complete ads from repeated or partial frames.
4. ChatGPT LLM parses and semantically dedupes the reconstructed ads.
5. Only LLM-reviewed records may be written to GitHub.

Do not tell the user that parsing must happen by a deterministic script first. The intended workflow is that ChatGPT performs semantic parsing in chat, then writes the structured result to the repository.

## Role of scripts

Scripts are allowed to:

- merge ChatGPT-approved records into `real_estate_ads.json`
- compute simple arithmetic such as `price_per_m2`
- validate JSON structure
- flag missing fields for LLM review
- generate stable IDs after the LLM has approved the semantic record
- rebuild static dashboard files

Scripts are not allowed to be the authority for:

- OCR from images/videos
- deciding what the ad says
- interpreting neighborhoods or landmarks
- interpreting non-standard prices
- deciding whether ambiguous records are duplicates
- correcting LLM interpretation without LLM review

## Current repository structure

- `real_estate_ads.json`
  - Main published ad database.
  - Contains `metadata` and an `ads` array.
  - Do not overwrite this large file from a stale local copy.

- `manual_ads.json`
  - Optional temporary staging file for small batches of ChatGPT-approved structured records.
  - Merge into `real_estate_ads.json`, then remove.

- `merge_manual_ads.py`
  - Mechanical storage/merge helper for ChatGPT-approved records.
  - It should not parse raw ads semantically.

- `build.py`
  - Regenerates static dashboard files from `real_estate_ads.json` and `page.template.html`.

- `page.template.html`
  - Dashboard template. Edit this for UI or dashboard logic changes, then run `python3 build.py`.

- `index.html`
  - GitHub Pages entry point generated from the template.

- `real_estate_ads.html`
  - Explicit generated dashboard file.

- `smoke_test.js`
  - Node-based smoke test for rendering/search/filter/table behavior. Update it when dashboard behavior changes.

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

For sale ads, these normally mean thousands of USD unless context clearly says otherwise:

- `100 الف` -> `100000`
- `400 الف` -> `400000`
- `575 الف` -> `575000`

Rule: if a sale ad has no `price_usd`, or has a suspiciously tiny sale price under `$5,000`, the LLM must re-read the full raw text for `عدد + الف/ألف/الاف` and infer thousands from context.

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

1. If the ad begins with or clearly contains `للإيجار`, `للاجار`, `للايجار`, or `ايجار`, classify as `إيجار`.
2. Only classify as `مطلوب شراء` if the phrase explicitly says `مطلوب شراء` or clearly asks to buy.
3. `مطلوب 400 دولار` by itself is an asking price.

### Area and neighborhood learning

If `area` or `area_group` is missing or ambiguous, the LLM should inspect full raw text, landmarks, and spelling variants.

Current examples:

- `شرقي ركن الدين`, `بشرقي ركن الدين`, `ركن الدين شرقي` -> likely `ركن الدين`, subarea `شرقي ركن الدين`
- `تنظيم كفرسوسة`, `تنظيم كفرسوسة شارع لافيولا` -> `كفرسوسة`, subarea `تنظيم كفرسوسة`
- `طلعة الميسات`, `دوار الميسات`, `قبل جامع ابو النور` -> usually `الميسات`
- `شعلان` -> `الشعلان`
- `جسر الأبيض`, `الجسر الأبيض` -> `الجسر الأبيض`
- `أبو رمانة`, `ابو رمانة` -> `أبو رمانة`
- `مزة`, `المزة`, `مزه` -> `المزة`
- `العدوي الفيلااات`, `العدوي الفيلات` -> `العدوي`, subarea `الفيلات`
- `شارع بغداد`, `بغداد` when clearly a Damascus area -> `شارع بغداد`

Capture landmarks as tags when useful, including: `جسر الحياة`, `جامع الإيمان`, `مرشد خاطر`, `مدرسة أنور العطار`, `الهجرة والجوازات`, `لافيولا`, `ماروتا سيتي`, and `جبل قاسيون`.

When uncertain, set the best area plus add `needs_review: true` and preserve the landmark in `tags`.

### Size extraction

Recognize size patterns such as:

- `80م`
- `80 م`
- `80 متر`
- `مساحة 300 متر`
- `المساحة 105م`
- `مساحة 200م²`

Do not confuse price thousands with square meters. Prefer size values near `مساحة`, `متر`, `م2`, `م²`, or `م`.

### Semantic dedupe

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
- `needs_review`, `review_reason`, `source_frame`, `source_frames`, `llm_reading_confidence` when confidence is imperfect

Always preserve `raw_text`. The app supports Arabic text and Arabic-Indic digits, so keep Arabic normalization behavior working when modifying search or parsing.

## Build and test commands

After data or template changes, run:

```bash
python3 build.py
node smoke_test.js
```

Generated dashboard files are `index.html` and `real_estate_ads.html`.

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
4. Prefer direct GitHub file edits for small files.
5. Use temporary workflows only for large generated files, mass repo-side rewrites, or cases where direct replacement is unsafe.
6. For new pasted WhatsApp ads, ChatGPT LLM parses the raw text here in chat first.
7. For screenshots/videos, ChatGPT LLM vision reads the frames here in chat first.
8. ChatGPT LLM decides semantic dedupe; scripts only provide hints.
9. Scripts may validate or normalize the LLM-parsed structured record, but should not override the semantic parse without checking the raw text/image.
10. Prefer durable context/rule updates over one-off corrections.
11. Run available tests when practical.
12. Summarize changed files and testing results.
13. Call out any assumptions or known limitations.
