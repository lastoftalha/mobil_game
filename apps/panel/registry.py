"""Panel kaynak tanımları.

Her kaynak (Resource) bir modelin panelde nasıl listeleneceğini, hangi alanların
hangi sekmede düzenleneceğini ve alt öğelerini (Inline) tanımlar. Genel görünümler
(views.py) bu tanımlara göre listeleme / ekleme / düzenleme / silme ekranlarını üretir.
"""
from dataclasses import dataclass, field
from typing import Callable, Optional

from apps.blog.models import Category, Post
from apps.contact.models import ContactMessage, Subscriber
from apps.content.models import (
    FAQ, Brand, GalleryCategory, GalleryImage, Project, ProjectCategory, ProjectImage, Service,
    ServiceFeature, ServiceOffering, ServiceStep, Testimonial,
)
from apps.core.models import NavItem, Office, Page, SocialLink


@dataclass
class Inline:
    model: type
    fields: list
    label: str
    item_label: str = "Öğe"
    fk_name: Optional[str] = None
    rich_fields: tuple = ()
    bulk_field: Optional[str] = None  # çoklu dosya yüklemeyle öğe oluşturma
    extra: int = 0

    @property
    def sortable(self):
        return any(f.name == "order" for f in self.model._meta.fields)

    @property
    def prefix(self):
        return self.model._meta.model_name


@dataclass
class Resource:
    key: str
    model: type
    label: str
    label_plural: str
    icon: str
    group: str
    list_display: list
    fieldsets: list = field(default_factory=list)
    search_fields: tuple = ()
    list_filters: tuple = ()
    rich_fields: tuple = ()
    fancy_fields: tuple = ()
    inlines: list = field(default_factory=list)
    toggle_fields: tuple = ("is_active",)
    can_create: bool = True
    can_delete: bool = True
    per_page: int = 40
    description: str = ""
    select_related: tuple = ()
    edit_url_name: str = "panel:edit"
    bulk_upload_field: Optional[str] = None
    bulk_upload_extra: tuple = ()  # toplu yüklemede seçilebilecek FK alanları
    export_csv: bool = False
    superuser_only: bool = False
    badge: Optional[Callable] = None  # menüde sayı rozeti

    @property
    def sortable(self):
        return any(f.name == "order" for f in self.model._meta.fields)

    @property
    def form_fields(self):
        result = []
        for _, fields in self.fieldsets:
            result.extend(fields)
        return result

    def field_label(self, name):
        if name == "__str__":
            return self.label
        try:
            return self.model._meta.get_field(name).verbose_name
        except Exception:
            return name


REGISTRY = {}
GROUPS = ["İçerik", "Blog", "Site", "Gelen kutusu"]


def register(resource):
    REGISTRY[resource.key] = resource
    return resource


SEO = ("SEO", ["meta_title", "meta_description"])

register(Resource(
    key="sayfalar", model=Page, label="Sayfa", label_plural="Sayfalar", icon="files", group="Site",
    list_display=[("title", "Sayfa"), ("slug", "Adres"), ("system_key", "Tür"), ("is_published", "Yayında"),
                  ("updated_at", "Güncellendi")],
    search_fields=("title", "slug"), toggle_fields=("is_published",), edit_url_name="panel:page_builder",
    description="Sitedeki tüm sayfalar. Bir sayfaya tıklayıp bölümlerini ekleyin, sıralayın ve düzenleyin.",
))

register(Resource(
    key="hizmetler", model=Service, label="Hizmet", label_plural="Hizmetler", icon="briefcase", group="İçerik",
    list_display=[("thumbnail", ""), ("title", "Hizmet"), ("show_on_home", "Ana sayfada"), ("is_active", "Aktif")],
    fieldsets=[
        ("Genel", ["title", "slug", "short_description", "tags", "is_active", "show_on_home"]),
        ("Görseller", ["thumbnail", "cover"]),
        ("Detay sayfası", ["intro", "overview"]),
        SEO,
    ],
    search_fields=("title", "tags"), rich_fields=("overview",), toggle_fields=("is_active", "show_on_home"),
    inlines=[
        Inline(ServiceFeature, ["title", "text"], "Özellikler", "Özellik"),
        Inline(ServiceOffering, ["title", "items"], "Ne sunuyoruz?", "Kart"),
        Inline(ServiceStep, ["title", "text"], "Çalışma süreci", "Adım"),
        Inline(FAQ, ["question", "answer", "is_active"], "Sıkça sorulan sorular", "Soru", fk_name="service"),
    ],
    description="Hizmet listesi, detay sayfaları, süreç adımları ve hizmete özel SSS.",
))

register(Resource(
    key="portfoy", model=Project, label="Proje", label_plural="Portföy", icon="folder-kanban", group="İçerik",
    list_display=[("cover", ""), ("title", "Proje"), ("category", "Kategori"), ("year", "Yıl"),
                  ("is_featured", "Öne çıkan"), ("is_active", "Aktif")],
    fieldsets=[
        ("Genel", ["title", "slug", "client", "category", "year", "summary", "is_active", "is_featured"]),
        ("Görsel & kart", ["cover", "strip_text", "strip_color"]),
        ("Detay", ["body", "services", "tags", "website_url"]),
        SEO,
    ],
    search_fields=("title", "client", "tags"), list_filters=("category", "is_featured"), rich_fields=("body",),
    toggle_fields=("is_active", "is_featured"), select_related=("category",),
    inlines=[Inline(ProjectImage, ["image", "caption"], "Proje görselleri", "Görsel", bulk_field="image")],
))

register(Resource(
    key="portfoy-kategorileri", model=ProjectCategory, label="Kategori", label_plural="Portföy kategorileri",
    icon="tags", group="İçerik", list_display=[("name", "Kategori"), ("slug", "Slug")],
    fieldsets=[("Genel", ["name", "slug"])], toggle_fields=(),
))

register(Resource(
    key="galeri", model=GalleryImage, label="Görsel", label_plural="Galeri", icon="images", group="İçerik",
    list_display=[("image", ""), ("title", "Başlık"), ("category", "Kategori"), ("is_active", "Aktif")],
    fieldsets=[("Genel", ["image", "title", "category", "is_active"])],
    search_fields=("title",), list_filters=("category",), select_related=("category",),
    bulk_upload_field="image", bulk_upload_extra=("category",),
    description="Görselleri sürükleyip bırakarak toplu yükleyebilirsiniz.",
))

register(Resource(
    key="galeri-kategorileri", model=GalleryCategory, label="Kategori", label_plural="Galeri kategorileri",
    icon="tags", group="İçerik", list_display=[("name", "Kategori"), ("slug", "Slug")],
    fieldsets=[("Genel", ["name", "slug"])], toggle_fields=(),
))

register(Resource(
    key="referanslar", model=Brand, label="Referans", label_plural="Referanslar", icon="award", group="İçerik",
    list_display=[("logo", ""), ("name", "Marka"), ("show_in_marquee", "Bantta"),
                  ("show_in_references", "Sayfada"), ("is_active", "Aktif")],
    fieldsets=[("Genel", ["name", "logo", "url", "monochrome", "show_in_marquee", "show_in_references", "is_active"])],
    search_fields=("name",), toggle_fields=("is_active", "show_in_marquee", "show_in_references"),
    bulk_upload_field="logo",
))

register(Resource(
    key="yorumlar", model=Testimonial, label="Yorum", label_plural="Müşteri yorumları",
    icon="message-square-quote", group="İçerik",
    list_display=[("avatar", ""), ("name", "Ad"), ("role", "Ünvan"), ("rating", "Puan"), ("is_active", "Aktif")],
    fieldsets=[("Genel", ["name", "role", "quote", "avatar", "rating", "metric_value", "metric_label", "is_active"])],
    search_fields=("name", "role", "quote"),
))

register(Resource(
    key="sss", model=FAQ, label="Soru", label_plural="Sıkça sorulan sorular", icon="circle-help", group="İçerik",
    list_display=[("question", "Soru"), ("service", "Hizmet"), ("is_active", "Aktif")],
    fieldsets=[("Genel", ["question", "answer", "service", "is_active"])],
    search_fields=("question", "answer"), list_filters=("service",), select_related=("service",),
    description="Hizmet seçilmeyen sorular genel SSS bölümlerinde gösterilir.",
))

register(Resource(
    key="blog", model=Post, label="Yazı", label_plural="Blog yazıları", icon="newspaper", group="Blog",
    list_display=[("cover", ""), ("title", "Başlık"), ("category", "Kategori"), ("status", "Durum"),
                  ("published_at", "Yayın tarihi"), ("views", "Okunma")],
    fieldsets=[
        ("İçerik", ["title", "slug", "category", "excerpt", "body", "tags"]),
        ("Yayın", ["status", "published_at", "is_featured", "author_name", "read_time", "cover"]),
        SEO,
    ],
    search_fields=("title", "excerpt", "tags"), list_filters=("category", "status"), rich_fields=("body",),
    toggle_fields=("is_featured",), select_related=("category",),
))

register(Resource(
    key="blog-kategorileri", model=Category, label="Kategori", label_plural="Blog kategorileri", icon="tags",
    group="Blog", list_display=[("name", "Kategori"), ("slug", "Slug")], fieldsets=[("Genel", ["name", "slug"])],
    toggle_fields=(),
))

register(Resource(
    key="menu", model=NavItem, label="Menü öğesi", label_plural="Menüler", icon="menu", group="Site",
    list_display=[("label", "Başlık"), ("url", "Bağlantı"), ("location", "Konum"), ("is_active", "Aktif")],
    fieldsets=[("Genel", ["location", "label", "url", "open_in_new_tab", "is_active"])],
    list_filters=("location",), search_fields=("label", "url"),
    description="Üst menü ve alt bilgideki site haritası bağlantıları. Sürükleyerek sıralayın.",
))

register(Resource(
    key="sosyal-medya", model=SocialLink, label="Hesap", label_plural="Sosyal medya", icon="share-2", group="Site",
    list_display=[("platform", "Platform"), ("url", "Bağlantı"), ("is_active", "Aktif")],
    fieldsets=[("Genel", ["platform", "label", "url", "is_active"])],
))

register(Resource(
    key="ofisler", model=Office, label="Ofis", label_plural="Ofisler", icon="map-pin", group="Site",
    list_display=[("name", "Ofis"), ("address", "Adres"), ("is_active", "Aktif")],
    fieldsets=[("Genel", ["name", "address", "phone", "email", "map_url", "dot_color", "is_active"])],
))

register(Resource(
    key="mesajlar", model=ContactMessage, label="Mesaj", label_plural="Mesajlar", icon="inbox",
    group="Gelen kutusu",
    list_display=[("name", "Gönderen"), ("email", "E-posta"), ("service", "Hizmet"), ("created_at", "Tarih"),
                  ("is_read", "Okundu")],
    search_fields=("name", "email", "company", "message"), list_filters=("is_read",), toggle_fields=("is_read",),
    can_create=False, edit_url_name="panel:message_detail", export_csv=True,
    badge=lambda: ContactMessage.objects.filter(is_read=False).count(),
))

register(Resource(
    key="aboneler", model=Subscriber, label="Abone", label_plural="Bülten aboneleri", icon="at-sign",
    group="Gelen kutusu",
    list_display=[("email", "E-posta"), ("created_at", "Kayıt tarihi"), ("is_active", "Aktif")],
    fieldsets=[("Genel", ["email", "is_active"])], search_fields=("email",), export_csv=True,
))


def grouped_registry(user):
    groups = []
    for group in GROUPS:
        items = [r for r in REGISTRY.values() if r.group == group and (not r.superuser_only or user.is_superuser)]
        if items:
            groups.append((group, items))
    return groups
