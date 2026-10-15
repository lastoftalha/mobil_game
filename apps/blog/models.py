import math
import re

from django.db import models
from django.urls import reverse
from django.utils import timezone
from django.utils.html import strip_tags

from apps.core.models import TimeStampedModel
from apps.core.utils import OptimizedImagesMixin, split_tags, unique_slug


class Category(models.Model):
    name = models.CharField("Kategori", max_length=100)
    slug = models.SlugField("Slug", max_length=120, unique=True, blank=True)
    order = models.PositiveIntegerField("Sıra", default=0)

    class Meta:
        ordering = ["order", "id"]
        verbose_name = "Blog kategorisi"
        verbose_name_plural = "Blog kategorileri"

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = unique_slug(self, self.name)
        super().save(*args, **kwargs)


class PostQuerySet(models.QuerySet):
    def published(self):
        return self.filter(status=Post.PUBLISHED, published_at__lte=timezone.now())


class Post(OptimizedImagesMixin, TimeStampedModel):
    DRAFT, PUBLISHED = "draft", "published"
    STATUS = [(DRAFT, "Taslak"), (PUBLISHED, "Yayında")]

    optimize_images = {"cover": 2000}

    title = models.CharField("Başlık", max_length=250)
    slug = models.SlugField("Adres (slug)", max_length=250, unique=True, blank=True)
    category = models.ForeignKey(Category, verbose_name="Kategori", on_delete=models.SET_NULL, null=True,
                                 blank=True, related_name="posts")
    cover = models.ImageField("Kapak görseli", upload_to="blog/", blank=True)
    excerpt = models.TextField("Özet", blank=True, help_text="Listelerde görünür. Boşsa metinden üretilir.")
    body = models.TextField("İçerik", blank=True)
    tags = models.CharField("Etiketler", max_length=300, blank=True, help_text="Virgülle ayırın.")
    author_name = models.CharField("Yazar", max_length=120, blank=True, default="Bitasarımlazım")
    read_time = models.PositiveSmallIntegerField("Okuma süresi (dk)", default=0, help_text="0 = otomatik hesapla")
    views = models.PositiveIntegerField("Görüntülenme", default=0)
    status = models.CharField("Durum", max_length=10, choices=STATUS, default=PUBLISHED)
    published_at = models.DateTimeField("Yayın tarihi", default=timezone.now)
    is_featured = models.BooleanField("Öne çıkar", default=False)
    meta_title = models.CharField("SEO başlık", max_length=200, blank=True)
    meta_description = models.TextField("SEO açıklama", blank=True)

    objects = PostQuerySet.as_manager()

    class Meta:
        ordering = ["-published_at", "-id"]
        verbose_name = "Blog yazısı"
        verbose_name_plural = "Blog yazıları"

    def __str__(self):
        return self.title

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = unique_slug(self, self.title)
        super().save(*args, **kwargs)

    def get_absolute_url(self):
        return reverse("blog:detail", args=[self.slug])

    @property
    def tag_list(self):
        return split_tags(self.tags)

    @property
    def summary(self):
        if self.excerpt:
            return self.excerpt
        text = re.sub(r"\s+", " ", strip_tags(self.body)).strip()
        return text[:220] + ("…" if len(text) > 220 else "")

    @property
    def minutes(self):
        if self.read_time:
            return self.read_time
        words = len(strip_tags(self.body).split())
        return max(1, math.ceil(words / 200))
