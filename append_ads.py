#!/usr/bin/env python3
"""Append WhatsApp-style Syrian real estate ads to real_estate_ads.json.

This script documents and implements the durable parsing workflow used when the
user pastes raw WhatsApp ads into ChatGPT:

1. Split the pasted text into one or more ad records.
2. Parse each ad into the project JSON schema.
3. Extract/repair key facts from raw Arabic text: transaction, type, area,
   price, size, floor, tags, photos, derived price/m2, score, and dedupe key.
4. Merge new records into real_estate_ads.json without duplicates.
5. Run build.py afterwards to regenerate CSV/HTML/index.

Important parser rule learned 2026-09-01:
Arabic price phrases like "100 الف", "100 ألف", "400 الف", "المطلوب 400 الف"
mean USD thousands in this dataset unless another currency is explicit. Do not
leave them blank and do not parse them as 100 or 400. Example: "100 الف وبازار"
=> price=100000, currency_norm=USD, price_usd=100000.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import subprocess
from datetime import datetime
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parent
DB_PATH = ROOT / "real_estate_ads.json"

AREA_ALIASES: dict[str, list[str]] = {
    "الميسات": ["الميسات", "ميسات", "دوار الميسات", "طلعة الميسات"],
    "ركن الدين": ["ركن الدين", "شرقي ركن الدين", "الشرقي ركن الدين"],
    "المالكي": ["المالكي", "مالكي"],
    "أبو رمانة": ["ابو رمانه", "أبو رمانة", "ابو رمانة", "أبو رمانه"],
    "الروضة": ["الروضه", "الروضة"],
    "المزرعة": ["المزرعه", "المزرعة"],
    "الشعلان": ["الشعلان", "شعلان"],
    "الجسر الأبيض": ["الجسر الابيض", "الجسر الأبيض", "جسر الابيض", "جسر الأبيض"],
    "الشهبندر": ["الشهبندر", "شهبندر"],
    "الصالحية": ["الصالحية", "صالحيه", "الصالحية"],
    "المهاجرين": ["المهاجرين", "مهاجرين"],
    "المزة": ["المزه", "المزة", "مزة", "مزه"],
    "كفرسوسة": ["كفرسوسه", "كفرسوسة"],
    "العدوي": ["العدوي", "عدوي"],
    "بغداد": ["شارع بغداد", "بغداد"],
    "خالدابن الوليد": ["خالدابن الوليد", "خالد ابن الوليد"],
    "ماروتا": ["ماروتا", "ماروتا سيتي"],
}

COMMERCIAL_WORDS = ["محل", "تجاري", "مستودع", "صالة", "مكتب", "عيادة", "شركة", "معهد"]
RESIDENTIAL_WORDS = ["شقه", "شقة", "بيت", "منزل", "فيلا", "دوبلكس"]
PHOTO_WORDS = ["يوجد صور", "صور", "فيديو", "فيديوللزبون", "فيديو للزبون"]
TAG_WORDS: dict[str, list[str]] = {
    "طابو أخضر": ["طابو اخضر", "طابو أخضر", "2400 سهم"],
    "سطح": ["سطح", "السطح"],
    "حديقة": ["حديقة", "جناين", "جنينه", "جنينة"],
    "مصعد": ["مصعد"],
    "قبو": ["قبو"],
    "مستودع": ["مستودع"],
    "تجاري": ["تجاري"],
    "صور": PHOTO_WORDS,
    "مدخل مستقل": ["مدخل مستقل"],
}

EASTERN_ARABIC = str.maketrans("٠١٢٣٤٥٦٧٨٩۰۱۲۳۴۵۶۷۸۹", "01234567890123456789")


def normalize(text: str) -> str:
    text = text.translate(EASTERN_ARABIC)
    text = re.sub(r"[\u0610-\u061a\u064b-\u065f\u0670ـ]", "", text)
    text = text.replace("أ", "ا").replace("إ", "ا").replace("آ", "ا").replace("ٱ", "ا")
    text = text.replace("ة", "ه").replace("ى", "ي").replace("ؤ", "و").replace("ئ", "ي")
    return re.sub(r"\s+", " ", text).strip().lower()


def split_ads(raw: str) -> list[str]:
    text = raw.strip()
    if not text:
        return []
    # WhatsApp exports may have blank lines between ads; single pasted ads often do not.
    parts = [p.strip() for p in re.split(r"\n\s*\n", text) if p.strip()]
    if len(parts) == 1:
        return parts
    return parts


def parse_price(raw: str, transaction_group: str) -> tuple[int | None, str, str, str | None, float | None]:
    text = normalize(raw)
    candidates: list[tuple[int, str]] = []
    # Explicit thousands: 100 الف / 100 ألف / 400 الف دولار / 1.5 مليون
    for m in re.finditer(r"(?<!\d)(\d+(?:[.,]\d+)?)\s*(الف|الاف|الفا|ألف|آلاف|مليون|ملايين)", text):
        n = float(m.group(1).replace(",", "."))
        unit = m.group(2)
        mult = 1_000_000 if "مليون" in unit or "ملايين" in unit else 1000
        candidates.append((int(n * mult), m.group(0)))
    # Compact numeric USD: 135000$ or 135 الف$ handled above.
    for m in re.finditer(r"(?<!\d)(\d{5,8})\s*(?:\$|دولار|usd)?", text):
        val = int(m.group(1))
        if val >= 10000:
            candidates.append((val, m.group(0)))
    if not candidates:
        return None, "", "", None, None
    # Prefer price around required/price words, otherwise first plausible candidate.
    chosen = candidates[0]
    for val, phrase in candidates:
        idx = text.find(phrase)
        window = text[max(0, idx - 40): idx + len(phrase) + 40]
        if any(w in window for w in ["مطلوب", "السعر", "منهي", "وبازار", "بازار"]):
            chosen = (val, phrase)
            break
    val, phrase = chosen
    price_text = raw.strip().split("\n")[-1] if "مطلوب" in raw or "السعر" in raw else phrase
    # In this project, real estate sale/rent prices written as "الف" are USD unless another currency is explicit.
    return val, "$", price_text, "USD", float(val)


def parse_size(raw: str) -> float | None:
    text = normalize(raw)
    patterns = [
        r"مساح[هة]\s*(\d+(?:[.,]\d+)?)\s*(?:متر|م2|م\b)",
        r"(?:^|\s)(\d+(?:[.,]\d+)?)\s*(?:متر|م2|م\b)",
    ]
    vals: list[float] = []
    for pat in patterns:
        for m in re.finditer(pat, text):
            val = float(m.group(1).replace(",", "."))
            if 8 <= val <= 2000:
                vals.append(val)
    return vals[0] if vals else None


def infer_area(raw: str) -> str:
    h = normalize(raw)
    for canonical, aliases in AREA_ALIASES.items():
        for alias in aliases:
            if normalize(alias) in h:
                return canonical
    return ""


def infer_transaction(raw: str) -> str:
    h = normalize(raw)
    if "للايجار" in h or "للاجار" in h or "للايجار" in h or "ايجار" in h:
        return "إيجار"
    if "مطلوب شراء" in h:
        return "مطلوب شراء"
    if "للبيع" in h or "بيع" in h:
        return "بيع"
    return ""


def infer_category(raw: str) -> str:
    h = normalize(raw)
    if any(normalize(w) in h for w in COMMERCIAL_WORDS):
        return "محل تجاري"
    if any(normalize(w) in h for w in RESIDENTIAL_WORDS):
        return "سكني"
    return ""


def infer_floor(raw: str) -> str:
    h = normalize(raw)
    parts: list[str] = []
    for label, words in {
        "أرضي": ["ارضي", "ارضيه"],
        "قبو": ["قبو"],
        "ملحق": ["ملحق"],
        "بلاطة كاملة": ["بلاطه كامله", "بلاطة كاملة"],
        "نزول شاحط": ["نزول شاحط", "شاحطين"],
    }.items():
        if any(normalize(w) in h for w in words):
            parts.append(label)
    m = re.search(r"طابق\s*(اول|ثاني|تاني|ثالث|تالت|رابع|خامس|سادس|\d+)", h)
    if m:
        parts.append("طابق " + m.group(1))
    return ", ".join(dict.fromkeys(parts))


def parse_tags(raw: str) -> list[str]:
    h = normalize(raw)
    tags: list[str] = []
    for tag, words in TAG_WORDS.items():
        if any(normalize(w) in h for w in words):
            tags.append(tag)
    return tags


def score_ad(ad: dict[str, Any]) -> int:
    score = 3
    if ad.get("price_usd") and ad.get("size_m2"):
        score += 1
    if ad.get("area_group") in {"المالكي", "أبو رمانة", "الروضة", "الميسات", "ركن الدين", "العدوي"}:
        score += 1
    if "طابو أخضر" in ad.get("tags", []):
        score += 1
    if ad.get("category_group") == "محل تجاري":
        score += 1
    if ad.get("price_per_m2") and ad["price_per_m2"] <= 1500 and ad.get("transaction_group") == "بيع":
        score += 1
    return max(1, min(score, 10))


def make_id(raw: str) -> str:
    return hashlib.sha1(normalize(raw).encode("utf-8")).hexdigest()[:10]


def parse_ad(raw: str, now: datetime) -> dict[str, Any]:
    trx = infer_transaction(raw)
    cat = infer_category(raw)
    area = infer_area(raw)
    price, currency, price_text, currency_norm, price_usd = parse_price(raw, trx)
    size = parse_size(raw)
    ppm = round(price_usd / size, 2) if price_usd and size and trx == "بيع" else None
    ad: dict[str, Any] = {
        "id": make_id(raw),
        "source": f"Manual ChatGPT paste {now.date().isoformat()}",
        "stamp_raw": now.strftime("%Y-%m-%d %H:%M"),
        "date_iso": now.isoformat(timespec="seconds"),
        "date": now.date().isoformat(),
        "transaction": trx,
        "transaction_group": trx,
        "category": cat,
        "category_group": cat,
        "area": area,
        "area_group": area,
        "price": price,
        "currency": currency,
        "currency_norm": currency_norm,
        "price_usd": price_usd,
        "price_text": price_text or "",
        "size_m2": size,
        "land_dunum": None,
        "floor": infer_floor(raw),
        "price_per_m2": ppm,
        "score": 0,
        "has_photos": any(normalize(w) in normalize(raw) for w in PHOTO_WORDS),
        "tags": parse_tags(raw),
        "dedupe_key": hashlib.sha1(normalize(raw).encode("utf-8")).hexdigest()[:12],
        "raw_text": raw.strip(),
    }
    ad["score"] = score_ad(ad)
    return ad


def load_db() -> dict[str, Any]:
    return json.loads(DB_PATH.read_text(encoding="utf-8"))


def save_db(db: dict[str, Any]) -> None:
    DB_PATH.write_text(json.dumps(db, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def append_ads(raw: str, run_build: bool = True) -> tuple[int, int]:
    db = load_db()
    ads = db.setdefault("ads", [])
    existing = {a.get("dedupe_key") for a in ads}
    now = datetime.now()
    added = 0
    skipped = 0
    for part in split_ads(raw):
        ad = parse_ad(part, now)
        if ad["dedupe_key"] in existing:
            skipped += 1
            continue
        ads.insert(0, ad)
        existing.add(ad["dedupe_key"])
        added += 1
    metadata = db.setdefault("metadata", {})
    metadata["record_count"] = len(ads)
    metadata["last_updated"] = now.date().isoformat()
    metadata["last_append"] = {
        "input_records": added + skipped,
        "added_records": added,
        "skipped_duplicates": skipped,
        "updated_at": now.isoformat(timespec="seconds"),
        "workflow": "ChatGPT pasted WhatsApp ads -> append_ads.py parser -> JSON -> build.py -> GitHub push",
    }
    save_db(db)
    if run_build:
        subprocess.run(["python3", "build.py"], cwd=ROOT, check=True)
    return added, skipped


def main() -> None:
    parser = argparse.ArgumentParser(description="Append pasted WhatsApp real estate ads.")
    parser.add_argument("input", nargs="?", help="Text file containing pasted ads. If omitted, read stdin.")
    parser.add_argument("--no-build", action="store_true", help="Do not run build.py after appending.")
    args = parser.parse_args()
    raw = Path(args.input).read_text(encoding="utf-8") if args.input else input()
    added, skipped = append_ads(raw, run_build=not args.no_build)
    print(f"added={added} skipped_duplicates={skipped}")


if __name__ == "__main__":
    main()
