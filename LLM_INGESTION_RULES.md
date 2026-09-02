# LLM Ingestion Rules

This project uses ChatGPT / LLM judgment as the authority for reading and interpreting Syrian real estate ads.

## Non-negotiable source-of-truth rules

1. **Images and videos must be read with LLM vision.**
   - Frame extraction/contact sheets may be mechanical.
   - Traditional OCR output may be used only as a rough hint.
   - The final readable text must be verified by ChatGPT vision/LLM from the image frames.
   - Do not add records to the database from unreviewed OCR text.

2. **Raw pasted text must be parsed by ChatGPT LLM.**
   - Python scripts, regex, or deterministic parsers are not the semantic authority.
   - Scripts may only help with formatting, storage, field validation, JSON merging, and obvious arithmetic.
   - If a script disagrees with the LLM interpretation, inspect the raw ad in ChatGPT and resolve it there.

3. **Deduplication must be decided by ChatGPT LLM.**
   - Deterministic dedupe keys are hints only.
   - The LLM must compare the meaningful ad content: neighborhood, area, price, size, floor, special features, and raw phrasing.
   - Do not discard an ad solely because a script says it is similar.
   - Do not add an ad solely because a generated ID is different.

4. **Neighborhood and price rules must be learned from the corpus.**
   - Syrian WhatsApp ads use inconsistent spellings, shorthand, local landmarks, typo-heavy text, and mixed Arabic/English symbols.
   - Treat this as an evolving LLM context problem, not a fixed regex problem.
   - When a new spelling, landmark, or price pattern appears, add it to these rules or `CODEX_CONTEXT.md`.

## Correct ingestion workflow

For pasted text:

1. User pastes one or more raw WhatsApp ads into ChatGPT.
2. ChatGPT LLM reads and separates the ads.
3. ChatGPT LLM parses each ad into structured fields.
4. ChatGPT LLM performs semantic dedupe against known/suspected existing ads.
5. ChatGPT writes only the approved structured records to GitHub.
6. Repo scripts may merge the approved records into `real_estate_ads.json`.

For screenshots/videos:

1. Extract frames or contact sheets only to make visual review possible.
2. ChatGPT vision reads the ad text from the frames.
3. ChatGPT LLM reconstructs complete ads from repeated/partial frames.
4. ChatGPT LLM parses and dedupes the reconstructed ads.
5. Only LLM-reviewed records may be written to GitHub.

## What scripts may do

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
- deciding whether two ambiguous records are duplicates
- correcting LLM interpretation without LLM review

## Neighborhood / area learning rules

Always preserve raw text and learn variants. Current examples:

- `شرقي ركن الدين`, `بشرقي ركن الدين`, `ركن الدين شرقي` -> likely `ركن الدين`, subarea `شرقي ركن الدين`
- `تنظيم كفرسوسة`, `تنظيم كفرسوسة شارع لافيولا` -> `كفرسوسة`, subarea `تنظيم كفرسوسة`
- `طلعة الميسات`, `دوار الميسات`, `قبل جامع ابو النور` -> usually `الميسات`
- `شعلان` -> `الشعلان`
- `جسر الأبيض`, `الجسر الأبيض` -> `الجسر الأبيض`
- `أبو رمانة`, `ابو رمانة` -> `أبو رمانة`
- `مزة`, `المزة`, `مزه` -> `المزة`
- `العدوي الفيلااات`, `العدوي الفيلات` -> `العدوي`, subarea `الفيلات`
- `شارع بغداد`, `بغداد` when clearly a Damascus area -> `شارع بغداد`
- Landmarks such as `جسر الحياة`, `جامع الإيمان`, `مرشد خاطر`, `مدرسة أنور العطار`, `الهجرة والجوازات`, and `لافيولا` should be captured as location tags even when the area is known.

When uncertain, set the best area plus add `needs_review: true` and preserve the landmark in `tags`.

## Price learning rules

WhatsApp prices are non-standard. The LLM must infer from full context.

Common sale-price patterns:

- `100 الف` -> `$100,000`
- `100 ألف` -> `$100,000`
- `400الف $` -> `$400,000`
- `400 الف$ وبازار` -> `$400,000`
- `المطلوب 400 الف منهي` -> `$400,000`, usually final/firm-ish because `منهي`
- `سعر 200 الف$ وبازار` -> `$200,000`
- `575 الف$ وبازار` -> `$575,000`

Common rent-price patterns:

- `مطلوب 400 دولار` in a rent ad -> rent price `$400`, not wanted purchase.
- `للإيجار` overrides the word `مطلوب` when `مطلوب` introduces the asking rent.

Rules:

- For sale ads, `الف/ألف/الاف` normally means thousands of USD unless the ad clearly says otherwise.
- Do not parse `100 الف` as `$100`.
- Do not parse a sale price under `$5,000` unless the raw text truly says a small price.
- `وبازار` means negotiable; keep it in `price_text` or tags.
- `منهي` means final/firm; keep it in `price_text` or tags.

## LLM dedupe rules

Two records may be duplicates if several of these match:

- same neighborhood/subarea or landmark
- same size
- same price
- same floor
- same room count
- same deed/title details
- same unusual phrases or features

Generated IDs are not dedupe evidence. OCR frame repetition is common; repeated visible ads from the same video should be merged into one reconstructed ad.

If uncertain, do not silently drop the record. Mark `needs_review: true` or keep both with a note explaining why.

## Review flags

Use these fields when confidence is imperfect:

- `needs_review: true`
- `review_reason`
- `source_frame` or `source_frames` for video/image-derived ads
- `llm_reading_confidence`: `high`, `medium`, or `low`

Do not let low-confidence OCR-derived records become normal records without LLM visual review.
