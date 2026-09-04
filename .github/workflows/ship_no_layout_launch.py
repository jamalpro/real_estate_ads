from pathlib import Path

OLD_TITLE = '<title>تقارير عقارات سوريا - قاعدة الإعلانات</title>'
NEW_TITLE = '''<title>تقرير عقارات دمشق | قاعدة إعلانات قابلة للبحث</title>
<meta name="description" content="تقرير عقارات دمشق: قاعدة إعلانات عقارية منظمة وقابلة للبحث لدمشق، تساعد على فلترة الإعلانات حسب المنطقة والسعر والمساحة ونوع العقار.">
<meta property="og:title" content="تقرير عقارات دمشق">
<meta property="og:description" content="بحث وفلترة ومقارنة لإعلانات عقارات دمشق في صفحة خفيفة وسريعة.">
<meta property="og:type" content="website">
<meta property="og:locale" content="ar_SY">
<meta name="twitter:card" content="summary">
<meta name="robots" content="index,follow">'''
OLD_H1 = '<h1>تقارير عقارات سوريا - قاعدة الإعلانات</h1>'
NEW_H1 = '<h1>تقرير عقارات دمشق</h1>'

for filename in ['page.template.html', 'index.html', 'real_estate_ads.html']:
    p = Path(filename)
    text = p.read_text(encoding='utf-8')
    if OLD_TITLE not in text:
        raise SystemExit(f'Expected original title not found in {filename}; refusing to patch layout unexpectedly')
    if OLD_H1 not in text:
        raise SystemExit(f'Expected original h1 not found in {filename}; refusing to patch layout unexpectedly')
    text = text.replace(OLD_TITLE, NEW_TITLE, 1)
    text = text.replace(OLD_H1, NEW_H1, 1)
    for forbidden in ['class="hero"', 'trust-grid', 'aboutModal', 'publicTrustNote', 'مشاركة الصفحة', 'أرسل إعلان / تصحيح']:
        if forbidden in text:
            raise SystemExit(f'Forbidden layout/UI marker introduced in {filename}: {forbidden}')
    p.write_text(text, encoding='utf-8')

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

smoke = Path('smoke_test.js')
if smoke.exists():
    s = smoke.read_text(encoding='utf-8')
    s = s.replace('تقارير عقارات سوريا - قاعدة الإعلانات', 'تقرير عقارات دمشق')
    smoke.write_text(s, encoding='utf-8')
