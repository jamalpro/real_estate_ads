#!/usr/bin/env python3
"""Rebuild real_estate_ads.json from existing raw_text using ChatGPT-approved rules.

Important project rule: ChatGPT/LLM is the semantic authority. This script is a
mechanical storage/formatting tool that applies the rules already approved in
LLM_INGESTION_RULES.md and DATABASE_REBUILD_STAGING.md at repository scale.
"""
from __future__ import annotations

import csv
import hashlib
import json
import re
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent
MAIN = ROOT / "real_estate_ads.json"
CSV = ROOT / "real_estate_ads.csv"
CORPUS = ROOT / "unified_raw_ads_corpus.txt"

DIGITS = str.maketrans("٠١٢٣٤٥٦٧٨٩۰۱۲۳۴۵۶۷۸۹", "01234567890123456789")

AREA_PATTERNS = [
    ("أبو رمانة", ["أبو رمانة", "ابو رمانة", "ابورمانة", "أبورمانة"]),
    ("المالكي", ["المالكي", "مالكي"]),
    ("الروضة", ["الروضة", "روضة"]),
    ("ماروتا", ["ماروتا", "ماروتا سيتي", "ماروتا ستي"]),
    ("المزرعة", ["المزرعة", "مزرعة", "مرشد خاطر", "جامع الايمان", "وزارة التربية"]),
    ("برنية", ["برنية", "برينيه", "برينية", "برنيه"]),
    ("شارع بغداد", ["شارع بغداد", "بغداد"]),
    ("الجسر الأبيض", ["الجسر الأبيض", "جسر الأبيض", "الجسر الابيض", "جسر الابيض"]),
    ("الشهبندر", ["الشهبندر", "شهبندر"]),
    ("الميسات", ["الميسات", "ميسات", "دوار الميسات", "طلعة الميسات", "جامع ابو النور", "جامع أبو النور", "قبل جامع ابو النور"]),
    ("العدوي", ["العدوي", "عدوي", "الفيلااات", "الفيلات", "جسر الحياة"]),
    ("المهاجرين", ["المهاجرين", "مهاجرين", "شورى", "نيربين"]),
    ("ركن الدين", ["ركن الدين", "شرقي ركن الدين", "بشرقي ركن الدين", "ركن الدين شرقي"]),
    ("كفرسوسة", ["كفرسوسة", "كفر سوسة", "تنظيم كفرسوسة", "لافيولا", "دوار كفرسوسة"]),
    ("المزة", ["المزة", "مزة", "مزه", "اوتستراد المزة", "مزة فيلات", "فيلات غربية", "فيلات شرقية"]),
    ("الشعلان", ["الشعلان", "شعلان", "حديقة السبكي"]),
    ("الصالحية", ["الصالحية", "صالحية"]),
    ("البرامكة", ["البرامكة", "برامكة"]),
    ("باب توما", ["باب توما"]),
    ("القنوات", ["القنوات"]),
    ("شارع الأمين", ["شارع الأمين", "شارع الامين"]),
    ("القصاع", ["القصاع", "قصاع"]),
    ("التجارة", ["التجارة", "تجارة", "مدرسة أنور العطار", "مدرسة انور العطار"]),
    ("الطلياني", ["الطلياني", "طلياني"]),
    ("عرنوس", ["عرنوس"]),
    ("ساروجة", ["ساروجة"]),
    ("الميدان", ["الميدان", "ميدان", "جزماتية"]),
    ("برزة", ["برزة", "برزه"]),
    ("خالد ابن الوليد", ["خالد ابن الوليد", "خالدابن الوليد"]),
    ("يعفور", ["يعفور"]),
    ("قرى الشام", ["قرى الشام", "قري الشام"]),
    ("الديماس", ["الديماس"]),
    ("دمر", ["دمر"]),
    ("قدسيا", ["قدسيا"]),
    ("ريف دمشق", ["ريف دمشق"]),
    ("الجبة", ["الجبة", "جبه", "تنظيم الجبة", "دوار تربية"]),
    ("القابون", ["القابون", "قابون", "أبو جرش", "ابو جرش"]),
    ("الزاهرة", ["الزاهرة", "زاهره", "زاهرة", "الزاهره"]),
    ("الحلبوني", ["الحلبوني", "حلبوني"]),
    ("باب شرقي", ["باب شرقي"]),
    ("باب مصلى", ["باب مصلى", "باب مصلا"]),
    ("القصور", ["القصور", "كازية القصور", "ساحة القصور"]),
    ("السبع بحرات", ["السبع بحرات", "سبع بحرات", "شارع الباكستان"]),
    ("شارع الثورة", ["شارع الثورة", "الثورة"]),
    ("شارع العابد", ["شارع العابد", "العابد"]),
    ("العمارة", ["العمارة", "مخفر العمارة"]),
    ("باب الجابية", ["باب الجابية", "باب الجابيه"]),
    ("الزبلطاني", ["الزبلطاني", "زبلطاني"]),
    ("داريا", ["داريا"]),
    ("القمرية", ["القمرية", "قمريه", "القمريه"]),
    ("وسط البلد", ["وسط البلد", "خلف القصر العدلي", "القصر العدلي", "الحريقة", "الحريقه"]),
    ("حاميش", ["حاميش", "مول قاسيون"]),
    ("شارع أسد الدين", ["اسد الدين", "أسد الدين", "شارع اسد الدين"]),
    ("الفيحاء", ["اوتوستراد الفيحاء", "استراد الفيحاء", "الفيحاء"]),
    ("طريق المطار", ["طريق المطار", "مفرق الاندلس"]),
]


def nd(s: str) -> str:
    return (s or "").translate(DIGITS)


def clean(s: str) -> str:
    s = (s or "").replace("\u200e", "").replace("\u200f", "")
    s = re.sub(r"\r\n?", "\n", s)
    s = re.sub(r"\n{3,}", "\n\n", s)
    return s.strip()


def norm(s: str) -> str:
    s = nd(s).lower()
    s = re.sub(r"[ًٌٍَُِّْـ]", "", s)
    s = s.replace("أ", "ا").replace("إ", "ا").replace("آ", "ا").replace("ى", "ي").replace("ة", "ه")
    s = re.sub(r"[\W_]+", " ", s, flags=re.UNICODE)
    return re.sub(r"\s+", " ", s).strip()


def infer_area(raw: str) -> str:
    n = norm(raw)
    best = ""
    best_len = 0
    for canon, patterns in AREA_PATTERNS:
        for p in patterns:
            pn = norm(p)
            if pn and pn in n and len(pn) > best_len:
                best = canon
                best_len = len(pn)
    return best


def infer_transaction(raw: str) -> tuple[str, str]:
    n = norm(raw)
    if "مطلوب للشراء" in n or "مطلوب شراء" in n:
        return "مطلوب شراء", "مطلوب شراء"
    sale = any(x in n for x in ["للبيع", "للييع", "البيع", "مبيع"])
    rent = any(x in n for x in ["للايجار", "للاجار", "للإيجار", "للآجار", "اجار", "ايجار", "آجار"])
    if sale and rent:
        return "بيع/إيجار", "بيع/إيجار"
    if rent:
        return "إيجار", "إيجار"
    if sale:
        return "بيع", "بيع"
    if "مطلوب" in n:
        return "مطلوب", "مطلوب"
    return "", ""


def infer_category(raw: str) -> tuple[str, str]:
    n = norm(raw)
    if "صيدليه" in n or "صيدلية" in raw:
        return "صيدلية/تجاري", "محل تجاري"
    if any(x in n for x in ["محل", "صاله", "صالة", "تجاري", "مستودع", "مكتب", "عيادات", "مركز طبي", "شركة", "شركه"]):
        return "تجاري", "محل تجاري"
    if any(x in n for x in ["فيلا", "فله", "فلة"]):
        return "فيلا", "سكني"
    if any(x in n for x in ["ارض", "دونم", "مزرعه", "مزرعة"]):
        return "أرض/مزرعة", "أرض"
    if any(x in n for x in ["شقه", "شقة", "منزل", "بيت", "دار", "طابق", "غرف"]):
        return "شقة/سكني", "سكني"
    return "", ""


def infer_size(raw: str) -> float | None:
    t = nd(raw)
    found = []
    for m in re.finditer(r"(?:المساحه|المساحة|مساحه|مساحة)?\s*[:：]?\s*([0-9]{1,4}(?:[\.,][0-9]+)?)\s*(?:متر|متر²|م٢|م2|م²|م\b)", t):
        val = float(m.group(1).replace(",", "."))
        if 10 <= val <= 5000:
            prefix = t[max(0, m.start() - 30):m.start()]
            found.append((0 if "مساح" in prefix else 1, val))
    if not found:
        return None
    found.sort(key=lambda x: x[0])
    return found[0][1]


def infer_land(raw: str) -> float | None:
    t = nd(raw)
    m = re.search(r"([0-9]+(?:[\.,][0-9]+)?)\s*دونم", t)
    return float(m.group(1).replace(",", ".")) if m else None


def infer_floor(raw: str) -> str:
    n = norm(raw)
    t = nd(raw)
    out = []
    if "ارضي" in n or "طابق ارضي" in n:
        out.append("أرضي")
    if "قبو" in n:
        out.append("قبو")
    if "ملحق" in n:
        out.append("ملحق")
    if "بلاطه كامله" in n or "بلاطة كاملة" in raw:
        out.append("بلاطة كاملة")
    ords = {"اول": "أول", "تاني": "ثاني", "ثاني": "ثاني", "تالت": "ثالث", "ثالث": "ثالث", "رابع": "رابع", "خامس": "خامس", "سادس": "سادس", "سابع": "سابع"}
    for k, v in ords.items():
        if re.search(r"(?:طابق|ط)\s*" + re.escape(k), n):
            out.append("طابق " + v)
            break
    m = re.search(r"(?:طابق|ط)\s*([0-9]{1,2})", t)
    if m and not any(x.startswith("طابق") for x in out):
        out.append("طابق " + m.group(1))
    uniq = []
    for x in out:
        if x not in uniq:
            uniq.append(x)
    return ", ".join(uniq)


def parse_price(raw: str, tg: str) -> tuple[float | None, str, str, float | None]:
    t = nd(raw)
    candidates: list[tuple[int, float, str]] = []

    def add(priority: int, value: float, text: str) -> None:
        if value and value > 0:
            candidates.append((priority, float(value), text.strip()))

    # USD million patterns only when explicitly marked with $/dollar.
    for m in re.finditer(r"([0-9]+(?:[\.,][0-9]+)?)\s*(?:مليون|ملايين)\s*(?:\$|دولار)(?:\s*(?:و|\+)\s*([0-9]{1,3}))?", t):
        val = float(m.group(1).replace(",", ".")) * 1_000_000
        if m.group(2):
            val += int(m.group(2)) * 1000
        add(1, val, m.group(0))
    for m in re.finditer(r"([0-9]+(?:[\.,][0-9]+)?)\s*(?:مليون|ملايين)\s*(?:و)?\s*([0-9]{1,3})\s*(?:الف|ألف|الاف)\s*(?:\$|دولار)", t):
        add(1, float(m.group(1).replace(",", ".")) * 1_000_000 + int(m.group(2)) * 1000, m.group(0))
    for m in re.finditer(r"([0-9]{1,3}(?:,[0-9]{3})+|[0-9]{5,8})\s*(?:\$|دولار)?", t):
        val = int(m.group(1).replace(",", ""))
        if val >= 10000:
            add(2, val, m.group(0))
    for m in re.finditer(r"000\s*([0-9]{1,3})\s*\$", t):
        add(1, int(m.group(1)) * 1000, m.group(0))
    for m in re.finditer(r"([0-9]+(?:[\.,][0-9]+)?)\s*\.?\s*(?:الف|ألف|الاف|آلاف)\s*(?:\$|دولار)?", t):
        add(1, float(m.group(1).replace(",", ".")) * 1000, m.group(0))
    for m in re.finditer(r"(?:المطلوب|مطلوب|السعر|سعر)\s*[:：]?\s*([0-9]{2,4})(?![0-9])(?!\s*(?:متر|م\b|غرف|طابق))", t):
        val = int(m.group(1))
        if tg in {"بيع", "بيع/إيجار", "مطلوب شراء"} and val < 5000:
            val *= 1000
        add(3, val, m.group(0))
    for m in re.finditer(r"([0-9]{3,4})\s*\$", t):
        add(4, int(m.group(1)), m.group(0))

    if not candidates:
        return None, "", "", None
    candidates.sort(key=lambda c: (c[0], -c[1] if tg in {"بيع", "بيع/إيجار", "مطلوب شراء"} else c[1]))
    _, value, text = candidates[0]
    return int(value) if abs(value - int(value)) < 1e-6 else value, "$", text, float(value)


def tags(raw: str) -> list[str]:
    n = norm(raw)
    out = []
    groups = [
        ("طابو أخضر", ["طابو اخضر", "طابواخضر"]),
        ("سطح", ["سطح", "حصة بسطح"]),
        ("قبو", ["قبو", "بلقبو"]),
        ("حديقة", ["حديقة", "جنينه", "جنينة"]),
        ("مصعد", ["مصعد"]),
        ("فيديو", ["فيديو", "فديو"]),
        ("صور", ["صور"]),
        ("تجاري", ["تجاري", "مكتب", "عيادات", "شركة", "صيدلية", "مستودع"]),
        ("مدخل مستقل", ["مدخل مستقل", "مدخلين"]),
        ("كراج", ["كراج"]),
        ("برندا", ["برندا", "برنده", "برندة"]),
    ]
    for tag, pats in groups:
        if any(norm(p) in n for p in pats):
            out.append(tag)
    return out


def has_photos(raw: str) -> bool:
    n = norm(raw)
    if "لا يوجد صور" in raw or "لايوجد صور" in raw:
        return False
    return any(x in n for x in ["يوجد صور", "صور", "فيديو", "فديو", "للزبون"])


def score(a: dict) -> int:
    s = 0
    if a.get("price_usd"):
        s += 2
    if a.get("size_m2"):
        s += 2
    if a.get("area_group"):
        s += 2
    if a.get("transaction_group"):
        s += 1
    if a.get("category_group"):
        s += 1
    if set(a.get("tags") or []) & {"طابو أخضر", "تجاري", "سطح", "قبو", "حديقة"}:
        s += 1
    if a.get("has_photos"):
        s += 1
    return min(s, 10)


def rebuild_ad(old: dict) -> dict:
    raw = clean(old.get("raw_text") or "")
    tx, tg = infer_transaction(raw)
    cat, cg = infer_category(raw)
    area = infer_area(raw)
    size = infer_size(raw)
    land = infer_land(raw)
    price, currency, price_text, price_usd = parse_price(raw, tg)
    floor = infer_floor(raw)
    pp = round(price_usd / size, 2) if price_usd and size and tg in {"بيع", "بيع/إيجار", "مطلوب شراء"} else None
    n = norm(raw)
    dedupe = hashlib.sha1("|".join([tg, cg, area, str(size or ""), str(int(price_usd) if price_usd else ""), n[:220]]).encode()).hexdigest()[:12]
    rid = hashlib.sha1((dedupe + n[:80]).encode()).hexdigest()[:10]
    conf = "high"
    if "OCR" in old.get("source", "") or "video" in old.get("source", "").lower():
        conf = "medium-low"
    if not price_usd or not size or not area:
        conf = "medium" if conf == "high" else conf
    new = {
        "id": rid,
        "source": old.get("source") or "rebuilt from raw_text",
        "stamp_raw": old.get("stamp_raw", ""),
        "date_iso": old.get("date_iso", ""),
        "date": old.get("date", ""),
        "transaction": tx,
        "transaction_group": tg,
        "category": cat,
        "category_group": cg,
        "area": area,
        "area_group": area,
        "price": price,
        "currency": currency,
        "currency_norm": "USD" if currency else None,
        "price_usd": price_usd,
        "price_text": price_text,
        "size_m2": size,
        "land_dunum": land,
        "floor": floor,
        "price_per_m2": pp,
        "score": 0,
        "has_photos": has_photos(raw),
        "tags": tags(raw),
        "parse_confidence": conf,
        "needs_review": conf != "high",
        "dedupe_key": dedupe,
        "raw_text": raw,
    }
    new["score"] = score(new)
    return new


def main() -> int:
    data = json.loads(MAIN.read_text(encoding="utf-8"))
    raw_ads = [a for a in data.get("ads", []) if a.get("raw_text")]
    rebuilt = []
    seen = set()
    duplicates = 0
    for old in raw_ads:
        raw_norm = norm(old.get("raw_text", ""))
        if any(x in raw_norm for x in ["سياره", "سيارة", "سكودا", "كودياك", "mg5", "نيسان جوك", "غيار زيت"]):
            continue
        a = rebuild_ad(old)
        key = (a["transaction_group"], a["category_group"], a["area_group"], a["size_m2"], int(a["price_usd"]) if a["price_usd"] else None, hashlib.sha1(raw_norm.encode()).hexdigest()[:12])
        if key in seen:
            duplicates += 1
            continue
        seen.add(key)
        rebuilt.append(a)

    rebuilt.sort(key=lambda x: (x.get("date") or "", x.get("source") or ""), reverse=True)
    meta = {
        "created_at": "2026-09-01",
        "rebuilt_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "record_count": len(rebuilt),
        "previous_record_count": data.get("metadata", {}).get("record_count", len(data.get("ads", []))),
        "source_files": ["existing real_estate_ads.json raw_text", "manual/chat/video records already merged before rebuild"],
        "rebuild_method": "ChatGPT LLM-directed rebuild using learned Syrian WhatsApp real-estate parsing rules; this script only applies approved rules mechanically.",
        "dedupe_method": "Semantic rule dedupe by area, size, price, transaction/category, and raw wording; old ids are not authoritative.",
        "duplicates_skipped": duplicates,
        "notes": "Production JSON intentionally replaced per user approval; Git history is the rollback. Video-derived records remain marked needs_review where source indicates OCR/video.",
    }
    MAIN.write_text(json.dumps({"metadata": meta, "ads": rebuilt}, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    fields = ["id", "date", "source", "transaction", "transaction_group", "category", "category_group", "area", "area_group", "price_usd", "price_text", "size_m2", "land_dunum", "floor", "price_per_m2", "score", "has_photos", "tags", "parse_confidence", "needs_review", "raw_text"]
    with CSV.open("w", encoding="utf-8-sig", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fields)
        w.writeheader()
        for a in rebuilt:
            row = {k: a.get(k) for k in fields}
            row["tags"] = "; ".join(a.get("tags") or [])
            w.writerow(row)

    corpus = []
    for i, a in enumerate(rebuilt, 1):
        corpus.append(f"===== RAW_AD_{i:04d} | {a.get('source','')} | {a.get('stamp_raw','')} | {a.get('parse_confidence','')} =====\n{a.get('raw_text','')}\n")
    CORPUS.write_text("\n".join(corpus), encoding="utf-8")

    stats = Counter(a.get("area_group") or "UNKNOWN" for a in rebuilt)
    print(f"Rebuilt {len(rebuilt)} records; skipped {duplicates} duplicates")
    print("Top areas:", stats.most_common(20))
    print("Needs review:", sum(bool(a.get("needs_review")) for a in rebuilt))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
