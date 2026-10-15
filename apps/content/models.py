from django.db import models
from django.urls import reverse

from apps.core.models import TimeStampedModel
from apps.core.utils import OptimizedImagesMixin, split_lines, split_tags, unique_slug


class Service(OptimizedImagesMixin, TimeStampedModel):
    optimize_images = {"thumbnail": 1400, "cover": 2400}

    title = models.CharField("Hizmet adı", max_length=200)
    slug = models.SlugField("Adres (slug)", max_length=200, unique=True, blank=True)
    short_description = models.TextField("Kısa açıklama", blank=True, help_text="Listelerde ve kartlarda görünür.")
    tags = models.CharField("Etiketler", max_length=300, blank=True, help_text="Virgülle ayırın.")
    thumbnail = models.ImageField("Liste görseli", upload_to="services/", blank=True)
    cover = models.ImageField("Detay kapak görseli", upload_to="services/", blank=True)
    intro = models.TextField("Detay giriş metni", blank=True, help_text="Detay sayfasının üstündeki açıklama.")
    overview = models.TextField("Genel bakış", blank=True)
    show_on_home = models.BooleanField("Ana sayfada göster", default=True)
    order = models.PositiveIntegerField("Sıra", default=0)
    is_active = models.BooleanField("Aktif", default=True)
    meta_title = models.CharField("SEO başlık", max_length=200, blank=True)
    meta_description = models.TextField("SEO açıklama", blank=True)

    class Meta:
        ordering = ["order", "id"]
        verbose_name = "Hizmet"
        verbose_name_plural = "Hizmetler"

    def __str__(self):
        return self.title

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = unique_slug(self, self.title)
        super().save(*args, **kwargs)

    def get_absolute_url(self):
        return reverse("content:service_detail", args=[self.slug])

    @property
    def tag_list(self):
        return split_tags(self.tags)

    @property
    def image(self):
        return self.cover or self.thumbnail

    @property
    def card_image(self):
        return self.thumbnail or self.cover


class ServiceFeature(models.Model):
    service = models.ForeignKey(Service, on_delete=models.CASCADE, related_name="features")
    title = models.CharField("Başlık", max_length=200)
    text = models.TextField("Açıklama", blank=True)
    order = models.PositiveIntegerField("Sıra", default=0)

    class Meta:
        ordering = ["order", "id"]
        verbose_name = "Özellik"
        verbose_name_plural = "Özellikler"

    def __str__(self):
        return self.title


class ServiceOffering(models.Model):
    service = models.ForeignKey(Service, on_delete=models.CASCADE, related_name="offerings")
    title = models.CharField("Başlık", max_length=200)
    items = models.TextField("Maddeler", blank=True, help_text="Her satıra bir madde.")
    order = models.PositiveIntegerField("Sıra", default=0)

    class Meta:
        ordering = ["order", "id"]
        verbose_name = "Sunduğumuz"
        verbose_name_plural = "Ne sunuyoruz"

    def __str__(self):
        return self.title

    @property
    def item_list(self):
        return [line.lstrip("+-• ").strip() for line in split_lines(self.items)]


class ServiceStep(models.Model):
    service = models.ForeignKey(Service, on_delete=models.CASCADE, related_name="steps")
    title = models.CharField("Adım", max_length=200)
    text = models.TextField("Açıklama", blank=True)
    order = models.PositiveIntegerField("Sıra", default=0)

    class Meta:
        ordering = ["order", "id"]
        verbose_name = "Süreç adımı"
        verbose_name_plural = "Süreç adımları"

    def __str__(self):
        return self.title


class FAQ(TimeStampedModel):
    question = models.CharField("Soru", max_length=300)
    answer = models.TextField("Cevap")
    service = models.ForeignKey(Service, verbose_name="Hizmet", on_delete=models.CASCADE, null=True, blank=True,
                                related_name="faqs", help_text="Boş bırakılırsa genel soru olur.")
    order = models.PositiveIntegerField("Sıra", default=0)
    is_active = models.BooleanField("Aktif", default=True)

    class Meta:
        ordering = ["order", "id"]
        verbose_name = "Sık sorulan soru"
        verbose_name_plural = "Sık sorulan sorular"

    def __str__(self):
        return self.question


class ProjectCategory(models.Model):
    name = models.CharField("Kategori", max_length=100)
    slug = models.SlugField("Slug", max_length=120, unique=True, blank=True)
    order = models.PositiveIntegerField("Sıra", default=0)

    class Meta:
        ordering = ["order", "id"]
        verbose_name = "Portföy kategorisi"
        verbose_name_plural = "Portföy kategorileri"

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = unique_slug(self, self.name)
        super().save(*args, **kwargs)


class Project(OptimizedImagesMixin, TimeStampedModel):
    optimize_images = {"cover": 2000}
    STRIP_COLORS = [
        ("brand", "Marka sarısı"), ("light", "Kırık beyaz"), ("gray", "Gri"), ("dark", "Siyah"),
    ]

    title = models.CharField("Proje adı", max_length=200)
    slug = models.SlugField("Adres (slug)", max_length=200, unique=True, blank=True)
    client = models.CharField("Müşteri / marka", max_length=200, blank=True)
    category = models.ForeignKey(ProjectCategory, verbose_name="Kategori", on_delete=models.SET_NULL,
                                 null=True, blank=True, related_name="projects")
    year = models.CharField("Yıl", max_length=10, blank=True)
    cover = models.ImageField("Kapak görseli", upload_to="portfolio/", blank=True)
    strip_text = models.CharField("Dikey şerit yazısı", max_length=40, blank=True,
                                  help_text="Kartın yanındaki dikey yazı; boşsa müşteri adı kullanılır.")
    strip_color = models.CharField("Şerit rengi", max_length=10, choices=STRIP_COLORS, default="brand")
    summary = models.TextField("Kısa açıklama", blank=True)
    body = models.TextField("Proje detayı", blank=True)
    services = models.ManyToManyField(Service, verbose_name="İlgili hizmetler", blank=True, related_name="projects")
    tags = models.CharField("Etiketler", max_length=300, blank=True, help_text="Virgülle ayırın.")
    website_url = models.URLField("Web sitesi", blank=True)
    is_featured = models.BooleanField("Ana sayfada öne çıkar", default=False)
    order = models.PositiveIntegerField("Sıra", default=0)
    is_active = models.BooleanField("Aktif", default=True)
    meta_title = models.CharField("SEO başlık", max_length=200, blank=True)
    meta_description = models.TextField("SEO açıklama", blank=True)

    class Meta:
        ordering = ["order", "-id"]
        verbose_name = "Proje"
        verbose_name_plural = "Portföy"

    def __str__(self):
        return self.title

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = unique_slug(self, self.title)
        super().save(*args, **kwargs)

    def get_absolute_url(self):
        return reverse("content:project_detail", args=[self.slug])

    @property
    def strip(self):
        return self.strip_text or self.client or self.title

    @property
    def tag_list(self):
        return split_tags(self.tags)


class ProjectImage(OptimizedImagesMixin, models.Model):
    optimize_images = {"image": 2200}

    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name="images")
    image = models.ImageField("Görsel", upload_to="portfolio/gallery/")
    caption = models.CharField("Açıklama", max_length=200, blank=True)
    order = models.PositiveIntegerField("Sıra", default=0)

    class Meta:
        ordering = ["order", "id"]
        verbose_name = "Proje görseli"
        verbose_name_plural = "Proje görselleri"

    def __str__(self):
        return self.caption or f"Görsel #{self.pk}"


class GalleryCategory(models.Model):
    name = models.CharField("Kategori", max_length=100)
    slug = models.SlugField("Slug", max_length=120, unique=True, blank=True)
    order = models.PositiveIntegerField("Sıra", default=0)

    class Meta:
        ordering = ["order", "id"]
        verbose_name = "Galeri kategorisi"
        verbose_name_plural = "Galeri kategorileri"

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = unique_slug(self, self.name)
        super().save(*args, **kwargs)


class GalleryImage(OptimizedImagesMixin, TimeStampedModel):
    optimize_images = {"image": 2200}

    image = models.ImageField("Görsel", upload_to="gallery/")
    title = models.CharField("Başlık", max_length=200, blank=True)
    category = models.ForeignKey(GalleryCategory, verbose_name="Kategori", on_delete=models.SET_NULL,
                                 null=True, blank=True, related_name="images")
    order = models.PositiveIntegerField("Sıra", default=0)
    is_active = models.BooleanField("Aktif", default=True)

    class Meta:
        ordering = ["order", "-id"]
        verbose_name = "Galeri görseli"
        verbose_name_plural = "Galeri"

    def __str__(self):
        return self.title or f"Görsel #{self.pk}"


class Brand(OptimizedImagesMixin, TimeStampedModel):
    optimize_images = {"logo": 800}

    name = models.CharField("Marka adı", max_length=120)
    logo = models.ImageField("Logo", upload_to="brands/")
    url = models.URLField("Web sitesi", blank=True)
    monochrome = models.BooleanField("Tek renk göster", default=False,
                                     help_text="Şeffaf PNG logolar için: koyu zeminde beyaz görünür.")
    show_in_marquee = models.BooleanField("Kayan bantta göster", default=True)
    show_in_references = models.BooleanField("Referanslar sayfasında göster", default=True)
    order = models.PositiveIntegerField("Sıra", default=0)
    is_active = models.BooleanField("Aktif", default=True)

    class Meta:
        ordering = ["order", "id"]
        verbose_name = "Referans / marka"
        verbose_name_plural = "Referanslar"

    def __str__(self):
        return self.name


class Testimonial(OptimizedImagesMixin, TimeStampedModel):
    optimize_images = {"avatar": 500}

    name = models.CharField("Ad soyad", max_length=120)
    role = models.CharField("Ünvan / firma", max_length=160, blank=True)
    quote = models.TextField("Yorum")
    avatar = models.ImageField("Fotoğraf", upload_to="testimonials/", blank=True)
    rating = models.PositiveSmallIntegerField("Puan (1-5)", default=5,
                                              choices=[(i, str(i)) for i in range(1, 6)])
    metric_value = models.CharField("Öne çıkan sonuç", max_length=30, blank=True, help_text="Örn: %80")
    metric_label = models.CharField("Sonuç açıklaması", max_length=120, blank=True)
    order = models.PositiveIntegerField("Sıra", default=0)
    is_active = models.BooleanField("Aktif", default=True)

    class Meta:
        ordering = ["order", "id"]
        verbose_name = "Müşteri yorumu"
        verbose_name_plural = "Müşteri yorumları"

    def __str__(self):
        return self.name

    @property
    def initials(self):
        return "".join(p[0] for p in self.name.split()[:2]).upper()

