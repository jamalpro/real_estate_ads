#!/usr/bin/env python3
"""Merge manual_ads.json into real_estate_ads.json.

This helper keeps the public app on a single database while still allowing
ChatGPT to stage newly parsed WhatsApp/OCR records in manual_ads.json. After a
successful merge, manual_ads.json is removed.
"""
from __future__ import annotations

import json
import re
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent
MAIN = ROOT / "real_estate_ads.json"
MANUAL = ROOT / "manual_ads.json"


def norm_text(value: object) -> str:
    text = str(value or "")
    text = re.sub(r"[\u064B-\u065F\u0610-\u061A\u06D6-\u06ED]", "", text)
    text = text.replace("أ", "ا").replace("إ", "ا").replace("آ", "ا")
    text = text.replace("ى", "ي").replace("ة", "ه")
    text = re.sub(r"\s+", " ", text)
    return text.strip().lower()


def keys_for(ad: dict) -> set[str]:
    """Return stable dedupe keys, preferring semantic/raw keys over unique IDs."""
    keys: set[str] = set()
    for field in ("dedupe_key", "raw_text"):
        value = ad.get(field)
        if value:
            keys.add(str(value))
            normalized = norm_text(value)
            if normalized:
                keys.add(normalized)
    # ID is intentionally last/fallback: OCR re-runs create new IDs for the same ad.
    if not keys and ad.get("id"):
        keys.add(str(ad["id"]))
    return keys


def main() -> int:
    if not MAIN.exists():
        raise SystemExit("real_estate_ads.json not found")
    if not MANUAL.exists():
        print("manual_ads.json not found; nothing to merge")
        return 0

    main_db = json.loads(MAIN.read_text(encoding="utf-8"))
    manual_db = json.loads(MANUAL.read_text(encoding="utf-8"))
    main_ads = main_db.setdefault("ads", [])
    manual_ads = manual_db.get("ads", [])

    seen: set[str] = set()
    for existing in main_ads:
        seen.update(keys_for(existing))

    added = 0
    skipped = 0
    for ad in manual_ads:
        kset = keys_for(ad)
        if not kset or any(k in seen for k in kset):
            skipped += 1
            continue
        ad = dict(ad)
        ad["source"] = ad.get("source") or "ChatGPT LLM parsed WhatsApp ad"
        main_ads.append(ad)
        seen.update(kset)
        added += 1

    meta = main_db.setdefault("metadata", {})
    meta["record_count"] = len(main_ads)
    meta["last_updated"] = datetime.now(timezone.utc).date().isoformat()
    meta["manual_ads_merged"] = {
        "merged_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "source_file": "manual_ads.json",
        "added_records": added,
        "skipped_duplicates": skipped,
    }
    note = meta.get("note", "")
    merge_note = " Manual ChatGPT records have been merged into this single database; manual_ads.json is retired."
    if merge_note.strip() not in note:
        meta["note"] = (note + merge_note).strip()

    MAIN.write_text(json.dumps(main_db, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    MANUAL.unlink()
    print(f"Merged {added} manual records; skipped {skipped}; total {len(main_ads)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
