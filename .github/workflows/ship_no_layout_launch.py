from pathlib import Path

TEMPLATE = Path('page.template.html')
text = TEMPLATE.read_text(encoding='utf-8')

old_title = '<title>تقارير عقارات سوريا - قاعدة الإعلانات</title>'
new_title = '''<title>تقرير عقارات دمشق | قاعدة إعلانات قابلة للبحث</title>
<meta name="description" content="تقرير عقارات دمشق: قاعدة إعلانات عقارية منظمة وقابلة للبحث لدمشق، تساعد على فلترة الإعلانات حسب المنطقة والسعر والمساحة ونوع العقار.">
<meta property="og:title" content="تقرير عقارات دمشق">
<meta property="og:description" content="بحث وفلترة ومقارنة لإعلانات عقارات دمشق في صفحة خفيفة وسريعة.">
<meta property="og:type" content="website">
<meta property="og:locale" content="ar_SY">
<meta name="twitter:card" content="summary">
<meta name="robots" content="index,follow">'''
if old_title not in text:
    raise SystemExit('Expected original title not found; refusing to patch layout unexpectedly')
text = text.replace(old_title, new_title, 1)

old_h1 = '<h1>تقارير عقارات سوريا - قاعدة الإعلانات</h1>'
new_h1 = '<h1>تقرير عقارات دمشق</h1>'
if old_h1 not in text:
    raise SystemExit('Expected original h1 not found; refusing to patch layout unexpectedly')
text = text.replace(old_h1, new_h1, 1)

# Guardrails: do not introduce visible launch UI/layout sections.
for forbidden in ['class="hero"', 'trust-grid', 'aboutModal', 'publicTrustNote', 'مشاركة الصفحة', 'أرسل إعلان / تصحيح']:
    if forbidden in text:
        raise SystemExit(f'Forbidden layout/UI marker introduced: {forbidden}')

TEMPLATE.write_text(text, encoding='utf-8')

Path('robots.txt').write_text(
    'User-agent: *\nAllow: /\nSitemap: https://jamalpro.github.io/real_estate_ads/sitemap.xml\n',
    encoding='utf-8',
)

Path('sitemap.xml').write_text('''<?xml version="1.0" encoding="UTF-8"?>
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
  <url>
    <loc>https://jamalpro.github.io/real_estate_ads/</loc>
    <changefreq>daily</changefreq>
    <priority>1.0</priority>
  </url>
</urlset>
''', encoding='utf-8')

Path('LAUNCH_NOTES.md').write_text('''# تقرير عقارات دمشق - Launch Notes

## Positioning

تقرير عقارات دمشق هو مرجع بحث ومقارنة لإعلانات عقارات دمشق. الهدف هو بناء ثقة وعادة استخدام، وليس تحقيق دخل من الإعلانات.

## Trust promise

- الصفحة ليست مكتباً عقارياً.
- النص الأصلي للإعلان يبقى ظاهراً للمراجعة.
- البيانات منظمة لتسهيل البحث والفلترة والمقارنة.
- الأسعار والملكية والموقع يجب التحقق منها قبل أي قرار.

## Initial launch channels

- مجموعات واتساب المهتمة بالعقارات في دمشق.
- مجموعات فيسبوك العقارية السورية.
- الأصدقاء والمعارف الباحثون عن شراء أو إيجار.

## Suggested launch copy

عملت صفحة بسيطة اسمها **تقرير عقارات دمشق** تجمع وتنظم إعلانات العقارات بدمشق، مع بحث وفلترة حسب المنطقة والسعر والمساحة ونوع العقار. الهدف مو مكتب عقاري ولا عمولة، بس مرجع مرتب بدل فوضى الواتساب. جرّبوها وإذا شفتوا خطأ أو إعلان مكرر خبروني.
''', encoding='utf-8')

# Smoke test title check only; do not add layout expectations beyond original UX.
smoke = Path('smoke_test.js')
if smoke.exists():
    s = smoke.read_text(encoding='utf-8')
    s = s.replace("تقارير عقارات سوريا - قاعدة الإعلانات", "تقرير عقارات دمشق")
    smoke.write_text(s, encoding='utf-8')
