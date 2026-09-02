#!/usr/bin/env python3
"""Merge manual_ads.json into real_estate_ads.json.

This is a one-time cleanup helper so all records live in a single database.
After a successful merge, manual_ads.json is removed.
"""
from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent
MAIN = ROOT / "real_estate_ads.json"
MANUAL = ROOT / "manual_ads.json"


def key_for(ad: dict) -> str:
    return str(ad.get("id") or ad.get("dedupe_key") or ad.get("raw_text") or "")


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

    seen = {key_for(ad) for ad in main_ads}
    added = 0
    skipped = 0
    for ad in manual_ads:
        k = key_for(ad)
        if not k or k in seen:
            skipped += 1
            continue
        ad = dict(ad)
        ad["source"] = ad.get("source") or "ChatGPT LLM parsed WhatsApp ad"
        main_ads.append(ad)
        seen.add(k)
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
