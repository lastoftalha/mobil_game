"""Sayfa oluşturucu bölüm tipleri.

Her bölüm tipi için: panelde hangi alanların gösterileceği, alan etiketleri,
alt öğe (SectionItem) kullanımı ve varsayılan tema burada tanımlanır.
Ön yüz şablonu: templates/site/sections/<tip>.html
"""

TITLE_HELP = "İpucu: [kelime] sarı vurgu kutusu, {kelime} serif yazı yapar. Yeni satır için Enter."

SECTION_TYPES = {
    "hero_home": {
        "label": "Ana Sayfa Hero",
        "icon": "sparkles",
        "description": "Sarı blok üzerinde dev başlık, sağda dikey görsel/video slaytı ve altta kayan bant.",
        "theme": "brand",
        "fields": ["title", "subtitle", "image", "video", "button_text", "button_url"],
        "labels": {
            "title": "Dev başlık",
            "subtitle": "Kayan bant metinleri (her satıra bir tane)",
            "image": "Yan görsel (slayt yoksa)",
            "video": "Yan video (mp4, isteğe bağlı)",
        },
        "items": {"label": "Yan slaytlar", "fields": ["image", "title"], "labels": {"title": "Alt yazı"}},
    },
    "page_hero": {
        "label": "Sayfa Başlığı (Hero)",
        "icon": "heading",
        "description": "İç sayfaların üst kısmı: büyük başlık, kısa açıklama ve isteğe bağlı görsel.",
        "theme": "dark",
        "fields": ["eyebrow", "title", "subtitle", "image"],
        "labels": {"eyebrow": "Üst etiket", "title": "Başlık", "subtitle": "Açıklama", "image": "Görsel (isteğe bağlı)"},
    },
    "statement": {
        "label": "Manifesto / Büyük Serif Metin",
        "icon": "quote",
        "description": "Ortalanmış, büyük serif başlık ve altında paragraf.",
        "theme": "dark",
        "fields": ["eyebrow", "title", "body", "button_text", "button_url"],
        "labels": {"title": "Büyük metin", "body": "Paragraf"},
    },
    "big_headline": {
        "label": "Dev Başlık + Metin",
        "icon": "type",
        "description": "Kalın dev başlık (vurgulu kelime destekli), serif alt başlık, paragraf ve buton.",
        "theme": "dark",
        "fields": ["title", "subtitle", "body", "button_text", "button_url"],
        "labels": {"title": "Dev başlık", "subtitle": "Serif alt başlık", "body": "Paragraf"},
    },
    "marquee_text": {
        "label": "Kayan Dev Yazı",
        "icon": "move-horizontal",
        "description": "Ekran boyunca akan büyük yazılar.",
        "theme": "brand",
        "fields": ["subtitle"],
        "labels": {"subtitle": "Kelimeler (her satıra bir tane)"},
    },
    "logo_marquee": {
        "label": "Referans Logo Bandı",
        "icon": "gallery-horizontal",
        "description": "Referanslar bölümündeki 'bantta göster' işaretli markalar kayarak gösterilir.",
        "theme": "dark",
        "fields": ["eyebrow", "title", "limit"],
    },
    "featured_work": {
        "label": "Öne Çıkan İşler",
        "icon": "layout-grid",
        "description": "Portföyde 'öne çıkan' işaretli projeler; dikey yazılı kartlar.",
        "theme": "dark",
        "fields": ["eyebrow", "title", "limit", "button_text", "button_url"],
    },
    "capabilities": {
        "label": "Hizmetler (Dönen Kelimeler)",
        "icon": "rotate-3d",
        "description": "Hizmet adları dönen kelimeler halinde, sağda açıklaması. Alt öğe eklenmezse 'ana sayfada göster' işaretli hizmetler kullanılır.",
        "theme": "light",
        "fields": ["eyebrow", "title", "subtitle", "button_text", "button_url"],
        "labels": {"subtitle": "Sağ taraftaki giriş metni"},
        "items": {"label": "Özel kelimeler (isteğe bağlı)", "fields": ["title", "text", "url"]},
    },
    "stats": {
        "label": "Rakamlar / İstatistik",
        "icon": "chart-no-axes-column",
        "description": "Sayaçlı rakamlar.",
        "theme": "brand",
        "fields": ["eyebrow", "title"],
        "items": {"label": "Rakamlar", "fields": ["value", "title", "text"], "labels": {"value": "Değer (ör. 600+)", "title": "Etiket"}},
    },
    "text_media": {
        "label": "Metin + Görsel",
        "icon": "panels-top-left",
        "description": "İki sütun: başlık, metin, butonlar ve görsel/video.",
        "theme": "dark",
        "fields": ["eyebrow", "title", "subtitle", "body", "image", "video", "button_text", "button_url", "button2_text", "button2_url", "flip"],
        "labels": {"subtitle": "Serif alt başlık", "flip": "Görsel solda olsun"},
        "items": {"label": "Madde listesi (isteğe bağlı)", "fields": ["title"]},
    },
    "features": {
        "label": "Özellik Kartları",
        "icon": "list-checks",
        "description": "Numaralı özellik/değer kartları.",
        "theme": "light",
        "fields": ["eyebrow", "title", "subtitle"],
        "items": {"label": "Kartlar", "fields": ["title", "text", "image", "url"]},
    },
    "process": {
        "label": "Çalışma Süreci",
        "icon": "milestone",
        "description": "Adım adım süreç.",
        "theme": "dark",
        "fields": ["eyebrow", "title", "subtitle"],
        "items": {"label": "Adımlar", "fields": ["title", "text"]},
    },
    "services_list": {
        "label": "Hizmet Listesi",
        "icon": "briefcase",
        "description": "Tüm aktif hizmetler büyük satırlar halinde.",
        "theme": "dark",
        "fields": ["eyebrow", "title", "subtitle", "limit"],
    },
    "portfolio_grid": {
        "label": "Portföy Izgarası",
        "icon": "layout-dashboard",
        "description": "Tüm projeler, kategori filtresiyle.",
        "theme": "dark",
        "fields": ["eyebrow", "title", "subtitle", "limit"],
    },
    "gallery_grid": {
        "label": "Foto Galeri",
        "icon": "images",
        "description": "Galeri görselleri, kategori filtresi ve büyütme (lightbox).",
        "theme": "dark",
        "fields": ["eyebrow", "title", "subtitle", "limit"],
    },
    "brands_grid": {
        "label": "Referans Logoları Izgarası",
        "icon": "award",
        "description": "'Referanslar sayfasında göster' işaretli markalar.",
        "theme": "light",
        "fields": ["eyebrow", "title", "subtitle", "limit"],
    },
    "testimonials": {
        "label": "Müşteri Yorumları",
        "icon": "message-square-quote",
        "description": "Aktif müşteri yorumları kaydırmalı gösterilir.",
        "theme": "dark",
        "fields": ["eyebrow", "title", "subtitle", "limit"],
        "labels": {"subtitle": "Puan metni (ör. 4,8/5 — 85 değerlendirme)"},
    },
    "faq": {
        "label": "Sıkça Sorulan Sorular",
        "icon": "circle-help",
        "description": "Alt öğe eklenirse onlar, eklenmezse SSS bölümündeki genel sorular gösterilir.",
        "theme": "light",
        "fields": ["eyebrow", "title", "subtitle", "limit", "button_text", "button_url"],
        "items": {"label": "Sorular (isteğe bağlı)", "fields": ["title", "text"], "labels": {"title": "Soru", "text": "Cevap"}},
    },
    "blog_latest": {
        "label": "Son Blog Yazıları",
        "icon": "newspaper",
        "description": "En son yayınlanan yazılar.",
        "theme": "dark",
        "fields": ["eyebrow", "title", "limit", "button_text", "button_url"],
    },
    "blog_list": {
        "label": "Blog Listesi",
        "icon": "rows-3",
        "description": "Kategori filtresi, arama ve sayfalama ile tüm yazılar.",
        "theme": "dark",
        "fields": ["limit"],
        "labels": {"limit": "Sayfa başına yazı"},
    },
    "contact_form": {
        "label": "İletişim Formu",
        "icon": "mail",
        "description": "İletişim formu, ofisler ve iletişim bilgileri.",
        "theme": "dark",
        "fields": ["eyebrow", "title", "subtitle", "body"],
        "labels": {"body": "Form üstü açıklama"},
    },
    "cta": {
        "label": "Harekete Geçirici Blok (CTA)",
        "icon": "megaphone",
        "description": "Dev başlık ve butonlu kapanış bloğu.",
        "theme": "brand",
        "fields": ["eyebrow", "title", "subtitle", "image", "button_text", "button_url", "button2_text", "button2_url"],
    },
    "image_band": {
        "label": "Tam Genişlik Görsel/Video",
        "icon": "image",
        "description": "Ekran genişliğinde görsel veya video bandı.",
        "theme": "dark",
        "fields": ["title", "image", "video"],
        "labels": {"title": "Alt yazı (isteğe bağlı)"},
    },
    "rich_text": {
        "label": "Serbest Metin",
        "icon": "file-text",
        "description": "KVKK, gizlilik vb. uzun metinler için.",
        "theme": "light",
        "fields": ["eyebrow", "title", "body"],
    },
}

SECTION_TYPE_CHOICES = [(key, cfg["label"]) for key, cfg in SECTION_TYPES.items()]

THEME_CHOICES = [
    ("dark", "Koyu (siyah)"),
    ("gray", "Koyu gri"),
    ("light", "Açık (kırık beyaz)"),
    ("brand", "Marka sarısı"),
]

# Bölüm modelindeki tüm içerik alanları (panelde tipe göre gizlenir/gösterilir)
SECTION_CONTENT_FIELDS = [
    "eyebrow", "title", "subtitle", "body", "image", "video", "button_text", "button_url",
    "button2_text", "button2_url", "limit", "flip",
]
ITEM_FIELDS = ["title", "subtitle", "text", "value", "image", "url"]
