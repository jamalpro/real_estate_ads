#!/usr/bin/env python3
"""Regenerate dashboard HTML files from real_estate_ads.json.

real_estate_ads.json is the single source of truth. This script recomputes
derived fields, validates the dataset, and writes both dashboard entry points:

- real_estate_ads.html for the explicit dashboard URL
- index.html for the GitHub Pages project root URL

Run it after any change to the JSON or to page.template.html.
"""

import json
import re
import sys
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parent
JSON_PATH = ROOT / "real_estate_ads.json"
HTML_PATH = ROOT / "real_estate_ads.html"
INDEX_PATH = ROOT / "index.html"
TEMPLATE_PATH = ROOT / "page.template.html"

# Variant labels that came from different ingest batches and mean the same thing.
# Edit these when a new batch introduces another spelling.
CATEGORY_GROUPS = {
    "محل": "محل تجاري",
    "محل/تجاري": "محل تجاري",
    "تجاري": "تجاري/مكتب",
    "تجاري/مكتب": "تجاري/مكتب",
}
TRANSACTION_GROUPS = {
    "بيع/إيجار": "بيع أو إيجار",
    "بيع أو إيجار": "بيع أو إيجار",
    "مطلوب": "مطلوب شراء",
    "مطلوب شراء": "مطلوب شراء",
    "": "غير محدد",
    "غير محدد": "غير محدد",
}

# "مطلوب 400$" means "asking 400$" in these ads, but the upstream parser read it as
# "wanted to buy". Only trust a buyer-wanted label when the text really says so.
# Matched against normalize_arabic() output, so hamza/ta-marbuta variants are already folded.
WANTED_RE = re.compile(r"للشرا|مطلوب\s*شرا")
RENT_RE = re.compile(r"ايجار|اجار|بالشهر|شهري")
SALE_RE = re.compile(r"بيع")
AMBIGUOUS_TRANSACTIONS = {"", "غير محدد", "مطلوب", "مطلوب شراء"}

AR_MARKS = re.compile(r"[ؐ-ًؚ-ٰٟـ]")
AR_DIGITS = str.maketrans("٠١٢٣٤٥٦٧٨٩۰۱۲۳۴۵۶۷۸۹", "01234567890123456789")


def normalize_arabic(value):
    text = AR_MARKS.sub("", str(value or ""))
    for src, dst in (("أإآٱ", "ا"), ("ى", "ي"), ("ؤ", "و"), ("ئ", "ي"), ("ة", "ه")):
        for ch in src:
            text = text.replace(ch, dst)
    return re.sub(r"\s+", " ", text.translate(AR_DIGITS)).strip().lower()


def area_key(value):
    key = normalize_arabic(value).replace(" ", "")
    return re.sub(r"^ال", "", key)


def build_area_groups(ads):
    """Elect one display label per normalized area key, most common variant wins."""
    variants = defaultdict(Counter)
    for ad in ads:
        area = (ad.get("area") or "").strip()
        if area:
            variants[area_key(area)][area] += 1
    labels, merges = {}, []
    for key, counts in variants.items():
        label = sorted(counts.items(), key=lambda kv: (-kv[1], -len(kv[0]), kv[0]))[0][0]
        labels[key] = label
        if len(counts) > 1:
            merges.append((label, sorted(counts)))
    return labels, merges


def resolve_transaction(ad):
    """Group a transaction label, re-reading raw_text when the label is unreliable."""
    stated = ad.get("transaction", "")
    group = TRANSACTION_GROUPS.get(stated, stated)
    if stated not in AMBIGUOUS_TRANSACTIONS:
        return group
    text = normalize_arabic(ad.get("raw_text", ""))
    if WANTED_RE.search(text):
        return "مطلوب شراء"
    rent, sale = bool(RENT_RE.search(text)), bool(SALE_RE.search(text))
    if rent and sale:
        return "بيع أو إيجار"
    if rent:
        return "إيجار"
    if sale:
        return "بيع"
    return "غير محدد"


def suspicious(ad):
    """Likely upstream price-parse errors, reported but never auto-corrected."""
    text = ad.get("price_text") or ""
    if re.search(r"\d\.\d{3}\b", text):
        return "thousands separator read as a decimal point"
    if re.search(r"\b0{2,3}\s+\d", text):
        return "digit groups appear reversed"
    if ad["transaction_group"] == "بيع" and ad["price_usd"] is not None and ad["price_usd"] < 5000:
        return "sale priced under $5,000"
    return None


def normalize_currency(ad):
    raw = (ad.get("currency") or "").strip()
    if raw in ("USD", "$"):
        return "USD"
    if raw.startswith("SYP"):
        return raw  # keeps the parser's "SYP?" uncertainty marker
    return None


def derive(ads):
    area_labels, merges = build_area_groups(ads)
    relabelled, flagged = [], []
    for ad in ads:
        currency = normalize_currency(ad)
        price = ad.get("price")
        ad["currency_norm"] = currency
        ad["price_usd"] = float(price) if currency == "USD" and price is not None else None
        ad["area_group"] = area_labels.get(area_key(ad.get("area") or ""), "")
        ad["category_group"] = CATEGORY_GROUPS.get(ad.get("category", ""), ad.get("category", ""))

        ad["transaction_group"] = resolve_transaction(ad)
        stated = TRANSACTION_GROUPS.get(ad.get("transaction", ""), ad.get("transaction", ""))
        if ad["transaction_group"] != stated:
            relabelled.append((ad["id"], stated or "(فارغ)", ad["transaction_group"]))

        # Only sales get a $/m2: mixing monthly rents into the same field made the
        # "cheapest per m2" sort return rentals every time.
        size = ad.get("size_m2")
        sale = ad["transaction_group"] == "بيع"
        ad["price_per_m2"] = round(ad["price_usd"] / size, 2) if sale and ad["price_usd"] and size else None

        reason = suspicious(ad)
        if reason:
            flagged.append((ad["id"], reason, (ad.get("price_text") or "").strip()[:48]))
    return merges, relabelled, flagged


def validate(db):
    ads = db["ads"]
    errors = []
    for field in ("id", "dedupe_key"):
        dupes = [v for v, n in Counter(a.get(field) for a in ads).items() if n > 1]
        if dupes:
            errors.append(f"duplicate {field}: {dupes[:5]}")
    missing = [a.get("id") for a in ads if not a.get("raw_text")]
    if missing:
        errors.append(f"ads with empty raw_text: {missing[:5]}")
    if errors:
        sys.exit("validation failed:\n  " + "\n  ".join(errors))
    db["metadata"]["record_count"] = len(ads)


def write_json(db):
    JSON_PATH.write_text(json.dumps(db, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def write_html(db):
    template = TEMPLATE_PATH.read_text(encoding="utf-8")
    if "{{ADS_JSON}}" not in template:
        sys.exit(f"{TEMPLATE_PATH.name} is missing the {{{{ADS_JSON}}}} placeholder")
    # '<' cannot appear raw inside the data island or it can close the script tag early.
    payload = json.dumps(db, ensure_ascii=False, separators=(",", ":")).replace("<", "\\u003c")
    html = template.replace("{{ADS_JSON}}", payload)
    HTML_PATH.write_text(html, encoding="utf-8")
    INDEX_PATH.write_text(html, encoding="utf-8")


def main():
    db = json.loads(JSON_PATH.read_text(encoding="utf-8"))
    ads = db["ads"]
    merges, relabelled, flagged = derive(ads)
    validate(db)
    write_json(db)
    write_html(db)

    print(f"{len(ads)} ads -> {HTML_PATH.name}, {INDEX_PATH.name}")
    print(f"  areas: {len({a['area_group'] for a in ads if a['area_group']})} groups"
          f" from {len({a['area'] for a in ads if a['area']})} raw labels")
    for label, variants in sorted(merges):
        print(f"    {label}  <-  {' / '.join(variants)}")
    print(f"  transaction relabelled from raw_text: {len(relabelled)}")
    for ad_id, before, after in relabelled:
        print(f"    {ad_id}  {before} -> {after}")
    no_price = sum(1 for a in ads if a["price_usd"] is None)
    print(f"  {no_price} ads have no USD price ({sum(1 for a in ads if a['currency_norm'] and a['currency_norm'] != 'USD')} priced in another currency)")
    print(f"  $/m² computed for {sum(1 for a in ads if a['price_per_m2'] is not None)} sale ads")
    if flagged:
        print(f"  {len(flagged)} ads flagged for review (upstream price parsing):")
        for ad_id, reason, text in flagged:
            print(f"    {ad_id}  {reason}  |  {text}")


if __name__ == "__main__":
    main()
