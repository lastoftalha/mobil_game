from django.core.validators import FileExtensionValidator, RegexValidator
from django.db import models
from django.urls import reverse

from .sections import SECTION_TYPE_CHOICES, SECTION_TYPES, THEME_CHOICES
from .utils import OptimizedImagesMixin, plain, split_lines, unique_slug

hex_color = RegexValidator(r"^#[0-9A-Fa-f]{6}$", "Renk #RRGGBB biçiminde olmalı.")
video_validator = FileExtensionValidator(["mp4", "webm"])


class TimeStampedModel(models.Model):
    created_at = models.DateTimeField("Oluşturulma", auto_now_add=True)
    updated_at = models.DateTimeField("Güncellenme", auto_now=True)

    class Meta:
        abstract = True


class SiteSettings(OptimizedImagesMixin, models.Model):
    """Tek kayıtlı (singleton) genel site ayarları."""

    optimize_images = {"og_image": 1600}

    # Genel
    site_name = models.CharField("Site adı", max_length=120, default="Bitasarımlazım")
    tagline = models.CharField("Slogan", max_length=200, blank=True, default="Bolu Sosyal Medya Ajansı")
    # Logolar
    logo = models.ImageField("Logo (koyu zemin)", upload_to="site/", blank=True,
                             help_text="Üst menüde kullanılır. Sarı veya beyaz logo önerilir.")
    logo_footer = models.ImageField("Alt bilgi logosu", upload_to="site/", blank=True,
                                    help_text="Sayfa altında büyük kullanılır.")
    logo_dark = models.ImageField("Logo (açık zemin)", upload_to="site/", blank=True,
                                  help_text="Açık arka planlarda kullanılır (siyah logo).")
    logo_mark = models.ImageField("Logo simgesi", upload_to="site/", blank=True,
                                  help_text="Sadece 'b' simgesi; menü kaydırılınca ve panelde kullanılır.")
    favicon = models.ImageField("Favicon", upload_to="site/", blank=True, help_text="Kare PNG, en az 180×180.")
    # Renkler
    color_primary = models.CharField("Ana renk (sarı)", max_length=7, default="#F6C500", validators=[hex_color])
    color_dark = models.CharField("Koyu renk", max_length=7, default="#0F1012", validators=[hex_color])
    color_gray = models.CharField("Gri", max_length=7, default="#2F3136", validators=[hex_color])
    color_light = models.CharField("Açık zemin", max_length=7, default="#F7F5F0", validators=[hex_color])
    # İletişim
    email = models.EmailField("E-posta", blank=True)
    email_secondary = models.EmailField("İkinci e-posta", blank=True)
    phone = models.CharField("Telefon", max_length=40, blank=True)
    phone_secondary = models.CharField("İkinci telefon", max_length=40, blank=True)
    whatsapp = models.CharField("WhatsApp numarası", max_length=40, blank=True,
                                help_text="Ülke koduyla, sadece rakam: 905462444414")
    show_whatsapp_button = models.BooleanField("Sabit WhatsApp butonu göster", default=True)
    # Üst menü
    header_cta_text = models.CharField("Menü butonu yazısı", max_length=60, blank=True, default="Bi Merhaba De")
    header_cta_url = models.CharField("Menü butonu bağlantısı", max_length=300, blank=True, default="/iletisim/")
    # Alt bilgi
    footer_about = models.TextField("Alt bilgi açıklaması", blank=True)
    footer_tagline = models.CharField("Alt bilgi serif yazı", max_length=200, blank=True)
    newsletter_enabled = models.BooleanField("Bülten kayıt formu", default=True)
    copyright_text = models.CharField("Telif metni", max_length=200, blank=True,
                                      default="© {yil} Bitasarımlazım. Tüm hakları saklıdır.",
                                      help_text="{yil} yazan yere otomatik olarak bu yıl gelir.")
    # SEO
    meta_title = models.CharField("Varsayılan sayfa başlığı", max_length=200, blank=True)
    meta_title_suffix = models.CharField("Başlık eki", max_length=80, blank=True, default=" | Bitasarımlazım")
    meta_description = models.TextField("Varsayılan meta açıklama", blank=True)
    meta_keywords = models.CharField("Anahtar kelimeler", max_length=300, blank=True)
    og_image = models.ImageField("Paylaşım görseli (OG)", upload_to="site/", blank=True,
                                 help_text="Sosyal medyada paylaşılınca görünen görsel (1200×630).")
    # Kodlar
    head_code = models.TextField("<head> içine kod", blank=True,
                                 help_text="Google Analytics, Meta Pixel vb. Sadece güvendiğiniz kodları ekleyin.")
    body_end_code = models.TextField("</body> öncesi kod", blank=True)
    # İletişim formu
    notify_email = models.EmailField("Form bildirim e-postası", blank=True,
                                     help_text="Yeni mesaj gelince bu adrese e-posta gönderilir.")
    contact_success_message = models.CharField(
        "Form başarı mesajı", max_length=300, blank=True,
        default="Mesajınız bize ulaştı. En kısa sürede size dönüş yapacağız.",
    )
    # Çerez bandı
    cookie_banner_enabled = models.BooleanField("Çerez bildirimi göster", default=True)
    cookie_text = models.CharField(
        "Çerez metni", max_length=400, blank=True,
        default="Sitemizde deneyiminizi iyileştirmek için çerezler kullanıyoruz.",
    )
    cookie_policy_url = models.CharField("Çerez politikası bağlantısı", max_length=300, blank=True)

    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Site ayarları"
        verbose_name_plural = "Site ayarları"

    def __str__(self):
        return "Site ayarları"

    def save(self, *args, **kwargs):
        self.pk = 1
        super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):  # pragma: no cover - singleton silinmez
        pass

    @classmethod
    def load(cls):
        obj, _ = cls.objects.get_or_create(pk=1)
        return obj

    @property
    def whatsapp_url(self):
        digits = "".join(c for c in self.whatsapp if c.isdigit())
        return f"https://wa.me/{digits}" if digits else ""

    @property
    def phone_href(self):
        return "".join(c for c in self.phone if c.isdigit() or c == "+")


class NavItem(models.Model):
    LOCATIONS = [("header", "Üst menü"), ("footer", "Alt bilgi (site haritası)")]

    location = models.CharField("Konum", max_length=20, choices=LOCATIONS, default="header")
    label = models.CharField("Başlık", max_length=80)
    url = models.CharField("Bağlantı", max_length=300, help_text="Örn: /hakkimizda/ veya https://...")
    open_in_new_tab = models.BooleanField("Yeni sekmede aç", default=False)
    order = models.PositiveIntegerField("Sıra", default=0)
    is_active = models.BooleanField("Aktif", default=True)

    class Meta:
        ordering = ["location", "order", "id"]
        verbose_name = "Menü öğesi"
        verbose_name_plural = "Menü öğeleri"

    def __str__(self):
        return self.label


class SocialLink(models.Model):
    PLATFORMS = [
        ("instagram", "Instagram"), ("facebook", "Facebook"), ("x", "X (Twitter)"),
        ("linkedin", "LinkedIn"), ("youtube", "YouTube"), ("tiktok", "TikTok"),
        ("behance", "Behance"), ("pinterest", "Pinterest"), ("whatsapp", "WhatsApp"), ("other", "Diğer"),
    ]

    platform = models.CharField("Platform", max_length=20, choices=PLATFORMS)
    label = models.CharField("Görünen ad", max_length=60, blank=True)
    url = models.URLField("Bağlantı")
    order = models.PositiveIntegerField("Sıra", default=0)
    is_active = models.BooleanField("Aktif", default=True)

    class Meta:
        ordering = ["order", "id"]
        verbose_name = "Sosyal medya hesabı"
        verbose_name_plural = "Sosyal medya hesapları"

    def __str__(self):
        return self.display_name

    @property
    def display_name(self):
        return self.label or self.get_platform_display()


class Office(models.Model):
    name = models.CharField("Ofis adı", max_length=80, help_text="Örn: Bolu")
    address = models.TextField("Adres")
    phone = models.CharField("Telefon", max_length=40, blank=True)
    email = models.EmailField("E-posta", blank=True)
    map_url = models.URLField("Harita bağlantısı", blank=True)
    map_embed = models.TextField("Harita gömme kodu (iframe)", blank=True)
    dot_color = models.CharField("Nokta rengi", max_length=7, default="#F6C500", validators=[hex_color])
    order = models.PositiveIntegerField("Sıra", default=0)
    is_active = models.BooleanField("Aktif", default=True)

    class Meta:
        ordering = ["order", "id"]
        verbose_name = "Ofis"
        verbose_name_plural = "Ofisler"

    def __str__(self):
        return self.name


class TextSnippet(models.Model):
    """Şablonlardaki sabit metinlerin panelden düzenlenebilen değerleri."""

    key = models.CharField("Anahtar", max_length=120, unique=True)
    value = models.TextField("Metin", blank=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["key"]
        verbose_name = "Sabit metin"
        verbose_name_plural = "Sabit metinler"

    def __str__(self):
        return self.key


class Page(OptimizedImagesMixin, TimeStampedModel):
    SYSTEM_KEYS = [
        ("home", "Ana Sayfa"), ("about", "Hakkımızda"), ("services", "Hizmetler"),
        ("portfolio", "Portföy"), ("gallery", "Galeri"), ("references", "Referanslar"),
        ("blog", "Blog"), ("contact", "İletişim"),
    ]

    optimize_images = {"og_image": 1600}

    title = models.CharField("Sayfa adı", max_length=200)
    slug = models.SlugField("Adres (slug)", max_length=200, unique=True, allow_unicode=False,
                            help_text="Sayfanın adresi: /slug/")
    system_key = models.CharField("Sistem sayfası", max_length=20, choices=SYSTEM_KEYS, blank=True, null=True,
                                  unique=True, editable=False)
    is_published = models.BooleanField("Yayında", default=True)
    show_in_sitemap = models.BooleanField("Site haritasında göster", default=True)
    meta_title = models.CharField("SEO başlık", max_length=200, blank=True)
    meta_description = models.TextField("SEO açıklama", blank=True)
    og_image = models.ImageField("Paylaşım görseli", upload_to="pages/", blank=True)

    class Meta:
        ordering = ["id"]
        verbose_name = "Sayfa"
        verbose_name_plural = "Sayfalar"

    def __str__(self):
        return self.title

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = unique_slug(self, self.title)
        super().save(*args, **kwargs)

    @property
    def is_system(self):
        return bool(self.system_key)

    @property
    def is_home(self):
        return self.system_key == "home"

    def get_absolute_url(self):
        if self.is_home:
            return reverse("core:home")
        return reverse("core:page", args=[self.slug])

    @property
    def seo_title(self):
        return plain(self.meta_title or self.title)


class Section(OptimizedImagesMixin, TimeStampedModel):
    optimize_images = {"image": 2400}

    page = models.ForeignKey(Page, verbose_name="Sayfa", on_delete=models.CASCADE, related_name="sections")
    type = models.CharField("Bölüm tipi", max_length=40, choices=SECTION_TYPE_CHOICES)
    name = models.CharField("Panel adı", max_length=120, blank=True,
                            help_text="Sadece panelde görünür; bölümleri ayırt etmek için.")
    theme = models.CharField("Arka plan", max_length=10, choices=THEME_CHOICES, blank=True)
    anchor = models.SlugField("Çapa (id)", max_length=60, blank=True, help_text="Bağlantı için: /sayfa/#capa")
    order = models.PositiveIntegerField("Sıra", default=0)
    is_active = models.BooleanField("Aktif", default=True)

    eyebrow = models.CharField("Üst etiket", max_length=120, blank=True)
    title = models.TextField("Başlık", blank=True)
    subtitle = models.TextField("Alt başlık", blank=True)
    body = models.TextField("Metin", blank=True)
    image = models.ImageField("Görsel", upload_to="sections/", blank=True)
    video = models.FileField("Video", upload_to="sections/video/", blank=True, validators=[video_validator])
    button_text = models.CharField("Buton yazısı", max_length=80, blank=True)
    button_url = models.CharField("Buton bağlantısı", max_length=300, blank=True)
    button2_text = models.CharField("2. buton yazısı", max_length=80, blank=True)
    button2_url = models.CharField("2. buton bağlantısı", max_length=300, blank=True)
    limit = models.PositiveSmallIntegerField("Gösterilecek adet", default=0, help_text="0 = tümü / varsayılan")
    flip = models.BooleanField("Ters düzen", default=False)

    class Meta:
        ordering = ["order", "id"]
        verbose_name = "Bölüm"
        verbose_name_plural = "Bölümler"

    def __str__(self):
        return self.display_name

    @property
    def config(self):
        return SECTION_TYPES.get(self.type, {})

    @property
    def type_label(self):
        return self.config.get("label", self.type)

    @property
    def display_name(self):
        return self.name or plain(self.title)[:60] or self.type_label

    @property
    def resolved_theme(self):
        return self.theme or self.config.get("theme", "dark")

    @property
    def lines(self):
        return split_lines(self.subtitle)

    def active_items(self):
        return [i for i in self.items.all() if i.is_active]


class SectionItem(OptimizedImagesMixin, models.Model):
    optimize_images = {"image": 2000}

    section = models.ForeignKey(Section, on_delete=models.CASCADE, related_name="items")
    title = models.CharField("Başlık", max_length=200, blank=True)
    subtitle = models.CharField("Alt başlık", max_length=200, blank=True)
    text = models.TextField("Metin", blank=True)
    value = models.CharField("Değer", max_length=40, blank=True)
    image = models.ImageField("Görsel", upload_to="sections/items/", blank=True)
    url = models.CharField("Bağlantı", max_length=300, blank=True)
    order = models.PositiveIntegerField("Sıra", default=0)
    is_active = models.BooleanField("Aktif", default=True)

    class Meta:
        ordering = ["order", "id"]
        verbose_name = "Bölüm öğesi"
        verbose_name_plural = "Bölüm öğeleri"

    def __str__(self):
        return self.title or f"Öğe #{self.pk}"
