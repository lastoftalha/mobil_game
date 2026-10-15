# Bitasarımlazım — Ajans Web Sitesi

Bitasarımlazım sosyal medya ajansının Django tabanlı web sitesi ve **özel yönetim paneli**.
Sitedeki her şey (sayfalar, bölümler, metinler, görseller, menüler, renkler, iletişim bilgileri, SEO)
`/panel/` adresindeki panelden yönetilir. Django'nun hazır admin paneli kullanılmaz.

Tasarım dili [billiondollarboy.com](https://www.billiondollarboy.com/) referans alınarak marka renkleriyle
(sarı `#F6C500`, koyu `#0F1012`, gri `#2F3136`) uyarlanmıştır. İçerikler eski siteden
(selim.bitasarimlazim.com) derlenmiştir.

## Özellikler

**Site**
- Dev, sıkışık başlıklar (Anton), zarif serif vurgular (Instrument Serif), renk bloklu bölümler
- Kayan logo/yazı bantları, dikey yazılı proje kartları, dönen hizmet kelimeleri, sayaçlar, lightbox galeri
- Ana sayfa, Hakkımızda, Hizmetler (+ detay), Portföy (+ detay), Galeri, Referanslar, Blog (+ detay, kategori, arama), İletişim
- Panelden sınırsız yeni sayfa (KVKK, kariyer vb.)
- İletişim formu (bot tuzağı + hız sınırı + e-posta bildirimi), bülten kaydı
- SEO: sayfa bazlı başlık/açıklama/paylaşım görseli, `sitemap.xml`, `robots.txt`, JSON-LD
- Mobil uyumlu, erişilebilir, `prefers-reduced-motion` desteği
- Panele giriş yapan kişi sitede gezerken "Bu sayfayı düzenle" kısayolunu görür

**Yönetim paneli (`/panel/`)**
- **Sayfa oluşturucu:** Her sayfa, sıralanabilir bölümlerden oluşur. 24 bölüm tipi var (hero, manifesto,
  dev başlık, logo bandı, öne çıkan işler, hizmet çarkı, rakamlar, metin+görsel, özellikler, süreç, SSS,
  yorumlar, blog, iletişim formu, CTA, görsel bandı, serbest metin…). Bölümler sürükle-bırak ile sıralanır,
  tek tıkla gizlenir/gösterilir, kopyalanır.
- Hizmetler (özellikler, "ne sunuyoruz" kartları, süreç adımları, hizmete özel SSS dahil), Portföy, Galeri
  (toplu yükleme), Referanslar, Müşteri yorumları, SSS, Blog (zengin metin editörü, görsel yükleme)
- Menüler, sosyal medya hesapları, ofisler
- **Site ayarları:** logolar, favicon, renkler (tüm siteye anında uygulanır), iletişim bilgileri, SEO,
  çerez bandı, özel kodlar (Analytics/Pixel)
- **Sabit metinler:** buton yazıları, form etiketleri gibi sitedeki tüm küçük metinler
- Gelen mesajlar (okundu/okunmadı, iç not, CSV dışa aktarma), bülten aboneleri
- Kullanıcı yönetimi (Yönetici / Editör yetkileri), şifre değiştirme
- Giriş denemesi sınırlaması, kaydedilmemiş değişiklik uyarısı, görsellerin otomatik küçültülmesi

### Başlık işaretleme dili

Başlık alanlarında:
- `[kelime]` → sarı vurgu kutusu
- `{kelime}` → ince serif yazı
- Enter → yeni satır

Örnek: `İyi işler şansa bırakılmaz, {bize bırakılır}`

## Hızlı başlatma (tek tık)

1. [Python 3.10+](https://www.python.org/downloads/) kurun (Windows'ta "Add python.exe to PATH" kutusunu işaretleyin).
2. Projeyi indirip klasöre çıkarın.
3. **Windows:** `baslat.bat` dosyasına çift tıklayın. **macOS / Linux:** terminalde `./baslat.sh` çalıştırın.

Betik her şeyi kurar, örnek içerikleri yükler ve siteyi tarayıcıda açar.
Panel girişi: kullanıcı `admin`, şifre `bitasarim2026`. İlk girişte panelde **Hesabım** sayfasından şifreyi değiştirin.

## Yerel kurulum (elle)

Python 3.10+ gerekir.

```bash
python -m venv .venv
source .venv/bin/activate            # Windows: .venv\Scripts\activate
pip install -r requirements.txt

cp .env.example .env                 # yerelde DJANGO_DEBUG=1 yapın
python manage.py migrate
python manage.py seed_site           # eski siteden derlenen örnek içerikleri yükler
python manage.py createsuperuser     # panel için yönetici hesabı
python manage.py runserver
```

- Site: http://127.0.0.1:8000/
- Panel: http://127.0.0.1:8000/panel/

`seed_site --reset` mevcut içerikleri silip örnek içerikleri yeniden yükler (kullanıcılar, mesajlar ve
aboneler korunur).

## Canlıya alma

1. Sunucuda projeyi klonlayın, sanal ortamı kurup `pip install -r requirements.txt` çalıştırın.
2. `.env.example` dosyasını `.env` olarak kopyalayın; `DJANGO_SECRET_KEY`, `DJANGO_ALLOWED_HOSTS`,
   `DJANGO_CSRF_TRUSTED_ORIGINS` ve SMTP ayarlarını doldurun.
   Gizli anahtar üretmek için:
   `python -c "import secrets; print(secrets.token_urlsafe(50))"`
3. Veritabanı ve statik dosyalar:
   ```bash
   python manage.py migrate
   python manage.py collectstatic --noinput
   python manage.py seed_site            # ilk kurulumda
   python manage.py createsuperuser
   ```
4. Uygulamayı gunicorn ile çalıştırın:
   ```bash
   gunicorn config.wsgi:application --bind 127.0.0.1:8000 --workers 3
   ```
5. Nginx örneği (statik dosyaları WhiteNoise sunar; medya dosyalarını Nginx sunar):
   ```nginx
   server {
       server_name bitasarimlazim.com www.bitasarimlazim.com;
       client_max_body_size 25M;

       location /media/ { alias /srv/bitasarim/media/; expires 30d; }
       location / {
           proxy_pass http://127.0.0.1:8000;
           proxy_set_header Host $host;
           proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
           proxy_set_header X-Forwarded-Proto $scheme;
       }
   }
   ```
   Nginx kullanmıyorsanız `.env` içinde `DJANGO_SERVE_MEDIA=1` yaparak medya dosyalarını Django'ya
   sundurabilirsiniz.

Varsayılan veritabanı SQLite'tır. PostgreSQL için `psycopg[binary]` paketini kurup `.env` içinde
`DB_ENGINE=postgresql` ve bağlantı bilgilerini verin.

**Yedekleme:** `db.sqlite3` (veya PostgreSQL veritabanı) ve `media/` klasörünü düzenli yedekleyin.

## Proje yapısı

```
config/            Django ayarları ve URL'ler
apps/core/         Site ayarları, menü, sayfa & bölüm modelleri, sabit metinler, seed komutu
apps/content/      Hizmetler, portföy, galeri, referanslar, yorumlar, SSS
apps/blog/         Blog yazıları ve kategoriler
apps/contact/      İletişim mesajları ve bülten aboneleri
apps/panel/        Özel yönetim paneli (kaynak kayıt sistemi, görünümler, formlar)
templates/site/    Ön yüz şablonları (sections/ = bölüm tipleri)
templates/panel/   Panel şablonları
static/site/       Sitenin CSS/JS/logo dosyaları
static/panel/      Panel CSS/JS ve kütüphaneler (Quill, SortableJS)
seed/              Örnek içerik görselleri ve blog yazıları
```

Yeni bir bölüm tipi eklemek için: `apps/core/sections.py` içine tanımı, `templates/site/sections/` içine
şablonu ekleyin; gerekiyorsa `apps/core/section_data.py` içine veri sağlayıcısını yazın.
Yeni bir içerik türünü panele eklemek için `apps/panel/registry.py` içinde `register(Resource(...))` yeterlidir.

## Testler

```bash
DJANGO_DEBUG=1 python manage.py test apps
```

## Notlar

- Eski sitedeki bazı içerikler yer tutucuydu (ör. web tasarım detay sayfası, bazı yorum isimleri,
  portföy açıklamaları). Bunlar anlamlı metinlerle dolduruldu; yayına almadan önce panelden gözden
  geçirmeniz önerilir.
- Portföyde "Erfelek Fındık" ve "Taksi Şimdi" projelerinin eski sitedeki görselleri sunucuda bulunamadığı
  için geçici kapak görselleri kullanıldı.
- KVKK sayfası taslak olarak oluşturuldu; metni hukuk danışmanınızla hazırlayıp yayına alın.
- İkonlar: [Lucide](https://lucide.dev) (ISC) ve [Simple Icons](https://simpleicons.org) (CC0).
  Editör: [Quill](https://quilljs.com) (BSD-3), sıralama: [SortableJS](https://sortablejs.github.io/Sortable/) (MIT).
