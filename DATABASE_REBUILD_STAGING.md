# Database Rebuild Staging

Created: 2026-09-01
Updated: 2026-09-01

## User request

The user wants a full database rebuild from all raw ad evidence available in ChatGPT:

1. Raw WhatsApp text pasted directly in chat.
2. Uploaded WhatsApp text dumps.
3. Uploaded WhatsApp screen-recording video frames, read by ChatGPT LLM Vision.
4. Existing `raw_text` fields already present in `real_estate_ads.json`.

The user explicitly requires:

- Image/video reading must be done by ChatGPT LLM Vision.
- Raw text parsing must be done by ChatGPT LLM, not by deterministic scripts.
- Deduplication must be semantic and decided by ChatGPT LLM, not by IDs/hashes alone.
- Scripts may only store, merge, format, validate arithmetic, and rebuild the static site.

## Replacement approval

The user confirmed that because all files are tracked in Git, it is safe to nuke/replace the current production JSON during the rebuild.

Practical meaning:

- `real_estate_ads.json` may be replaced by the rebuilt database after a best-effort LLM-reviewed rebuild pass.
- The old database does not need to be preserved inside the repository as a separate backup file because Git history is the backup.
- Replacement should still be made in a clear commit with a descriptive message so rollback is easy.

## Important safety rule

The previous safety rule was: do not overwrite `real_estate_ads.json` until the rebuilt database is more reliable than the current production database.

After user approval, this changes to:

- It is acceptable to replace `real_estate_ads.json` once the rebuild pass is complete enough to be useful.
- The replacement commit must be easy to identify and revert.
- Any records from video frames that were not visually reviewed by ChatGPT LLM Vision must be marked as lower confidence or excluded.

The current production database had `record_count: 222` when this staging note was created. It contains useful existing raw text but also known parsing errors, including Arabic thousand-price misses and rent/wanted-buy confusion.

## Raw source inventory found in ChatGPT/File Library

### Uploaded WhatsApp text dump: Aug 5-25

File title: `Pasted text.txt`

This contains ads beginning around 2026-08-05 and includes many sale/rent records, duplicates, non-real-estate noise, and truncated WhatsApp `Read more` sections.

### Uploaded WhatsApp text dump: Aug 25-Sep 1

File title: `Pasted text.txt`

This contains newer ads from around 2026-08-25 through 2026-09-01, including many records already partly represented in `real_estate_ads.json`.

### Uploaded WhatsApp MP4 screen recording

The MP4 must be processed by extracting visual frames/contact sheets only. Final OCR/reading must be done by ChatGPT LLM Vision.

Earlier scripted/OCR batches are not authoritative and should be treated as `needs_review` unless visually re-read by ChatGPT LLM Vision.

### Existing database raw_text

`real_estate_ads.json` currently contains `raw_text` for the production records. These can be used as raw evidence, but their structured fields must not be blindly trusted during rebuild.

## Rebuild process to follow

1. Build a unified raw corpus text file from all accessible raw sources.
2. Preserve provenance for each raw item:
   - uploaded text dump name/date range
   - chat-pasted ad
   - video frame/contact-sheet reference
   - existing database raw_text
3. First LLM pass: split raw corpus into candidate ad blocks.
4. Second LLM pass: remove obvious non-real-estate noise such as cars unless intentionally relevant.
5. Third LLM pass: semantic deduplication using neighborhood, size, price, unique features, and repeated timestamps.
6. Fourth LLM pass: parse structured fields.
7. Fifth LLM pass: learn/update neighborhood and price rules from the corpus.
8. Sixth LLM pass: re-parse uncertain records using the learned rules.
9. Quality gate before replacing production JSON:
   - record count should be plausible against source corpus
   - known bug examples must parse correctly
   - spot checks from each source batch should pass where practical
   - no blind script/OCR-derived records should be included as high confidence without LLM review
10. Replace `real_estate_ads.json` in one clear commit after the rebuild pass.

## Known examples that must parse correctly

- `100 الف وبازار` in a sale ad means `$100,000`, not null or `$100`.
- `مطلوب 400 دولار` in an `للإيجار` ad is rent price, not wanted-purchase.
- `السعر : 000 36$` likely means `$36,000` annual rent in context, not `$36`.
- `3 مليون$ و 300` likely means `$3,300,000` or needs LLM review, not `$3`.
- `مطلوب ٣٢٥` in sale context usually means `$325,000` when neighborhood/size indicates real estate sale.
- `١١٠وسكرة` in sale context usually means `$110,000`.

## Status

This file is a staging/rebuild guardrail. The user has approved replacing the current production JSON because Git history provides rollback.

Production JSON should be replaced only by a clear rebuild commit, not by accidental stale-file overwrite.