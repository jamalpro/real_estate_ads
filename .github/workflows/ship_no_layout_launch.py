from pathlib import Path
import re

NEW_TITLE_TEXT = 'تقرير عقارات دمشق | قاعدة إعلانات قابلة للبحث'
NEW_DESCRIPTION = 'تقرير عقارات دمشق: قاعدة إعلانات عقارية منظمة وقابلة للبحث لدمشق، تساعد على فلترة الإعلانات حسب المنطقة والسعر والمساحة ونوع العقار.'
OG_BLOCK = '''<meta property="og:title" content="تقرير عقارات دمشق">
<meta property="og:description" content="بحث وفلترة ومقارنة لإعلانات عقارات دمشق في صفحة خفيفة وسريعة.">
<meta property="og:type" content="website">
<meta property="og:locale" content="ar_SY">
<meta name="twitter:card" content="summary">
<meta name="robots" content="index,follow">'''


def patch_head(text):
    text = re.sub(r'<title>.*?</title>', f'<title>{NEW_TITLE_TEXT}</title>', text, count=1, flags=re.S)
    if re.search(r'<meta name="description" content="[^"]*">', text):
        text = re.sub(r'<meta name="description" content="[^"]*">', f'<meta name="description" content="{NEW_DESCRIPTION}">', text, count=1)
    else:
        text = text.replace(f'<title>{NEW_TITLE_TEXT}</title>', f'<title>{NEW_TITLE_TEXT}</title>\n<meta name="description" content="{NEW_DESCRIPTION}">', 1)
    if 'property="og:title"' not in text:
        text = text.replace(f'<meta name="description" content="{NEW_DESCRIPTION}">', f'<meta name="description" content="{NEW_DESCRIPTION}">\n{OG_BLOCK}', 1)
    return text


def patch_brand_text(text):
    text = text.replace('<h1>تقارير عقارات سوريا - قاعدة الإعلانات</h1>', '<h1>تقرير عقارات دمشق</h1>')
    text = text.replace('<div class="kicker">تقارير عقارات سوريا</div>', '<div class="kicker">تقرير عقارات دمشق</div>')
    return text

for filename in ['page.template.html', 'index.html', 'real_estate_ads.html']:
    p = Path(filename)
    text = p.read_text(encoding='utf-8')
    before = text
    text = patch_head(text)
    text = patch_brand_text(text)
    # Explicit guardrails: do not add new visible launch UI or extra controls.
    for forbidden in ['publicTrustNote', 'عن المؤشر والمنهجية', 'مشاركة الصفحة', 'أرسل إعلان / تصحيح', 'trust-card']:
        if forbidden in text:
            raise SystemExit(f'Forbidden new launch UI marker found in {filename}: {forbidden}')
    if text == before:
        raise SystemExit(f'No changes made to {filename}')
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
    s = s.replace('تقارير عقارات سوريا | Real Estate Ads', NEW_TITLE_TEXT)
    smoke.write_text(s, encoding='utf-8')
