import re
from io import BytesIO

from django.core.files.base import ContentFile
from django.utils.html import escape
from django.utils.safestring import mark_safe
from django.utils.text import slugify

TR_MAP = str.maketrans({
    "ç": "c", "Ç": "c", "ğ": "g", "Ğ": "g", "ı": "i", "I": "i", "İ": "i",
    "ö": "o", "Ö": "o", "ş": "s", "Ş": "s", "ü": "u", "Ü": "u", "â": "a", "î": "i", "û": "u",
})


def tr_slugify(value):
    """Türkçe karakterleri ASCII karşılıklarına çevirerek slug üretir."""
    return slugify(str(value or "").translate(TR_MAP))


def unique_slug(instance, value, field="slug", max_length=200):
    base = tr_slugify(value)[: max_length - 6] or "icerik"
    slug = base
    model = type(instance)
    n = 2
    while model.objects.filter(**{field: slug}).exclude(pk=instance.pk).exists():
        slug = f"{base}-{n}"
        n += 1
    return slug


def tr_upper(value):
    """Türkçe büyük harf dönüşümü (i -> İ, ı -> I)."""
    return str(value or "").replace("i", "İ").replace("ı", "I").upper()


_HL_RE = re.compile(r"\[(.+?)\]")
_SERIF_RE = re.compile(r"\{(.+?)\}")


def fancy(value):
    """Başlık işaretleme dili.

    [kelime]  -> sarı vurgulu kutu
    {kelime}  -> serif (ince, zarif) yazı
    Satır sonları <br> olur. Önce HTML kaçışlanır; güvenlidir.
    """
    text = escape(str(value or "").strip())
    text = _HL_RE.sub(r'<mark class="hl">\1</mark>', text)
    text = _SERIF_RE.sub(r'<em class="serif">\1</em>', text)
    text = text.replace("\r\n", "\n").replace("\n", "<br>")
    return mark_safe(text)


def plain(value):
    """İşaretleme karakterlerini temizler (meta başlıklar vb. için)."""
    return re.sub(r"[\[\]{}]", "", str(value or "")).replace("\n", " ").strip()


def optimized_content(fileobj, name, max_px=2000):
    """Görsel max_px'ten büyükse küçültülmüş ContentFile döndürür, değilse None."""
    try:
        from PIL import Image, ImageOps
    except ImportError:  # pragma: no cover
        return None
    try:
        fileobj.seek(0)
        img = Image.open(fileobj)
        fmt = (img.format or "").upper()
        if fmt not in ("JPEG", "PNG", "WEBP") or getattr(img, "is_animated", False) or max(img.size) <= max_px:
            return None
        img = ImageOps.exif_transpose(img)
        img.thumbnail((max_px, max_px))
        buf = BytesIO()
        if fmt == "JPEG":
            if img.mode not in ("RGB", "L"):
                img = img.convert("RGB")
            img.save(buf, "JPEG", quality=84, optimize=True, progressive=True)
        elif fmt == "WEBP":
            img.save(buf, "WEBP", quality=84)
        else:
            img.save(buf, "PNG", optimize=True)
        return ContentFile(buf.getvalue(), name=name)
    except Exception:
        return None
    finally:
        try:
            fileobj.seek(0)
        except Exception:
            pass


def optimize_image(field_file, max_px=2000):
    """Yeni yüklenen görseli makul boyuta indirir ve sıkıştırır."""
    new = optimized_content(field_file, field_file.name, max_px)
    if new is not None:
        field_file.file = new


class OptimizedImagesMixin:
    """Model kaydedilirken belirtilen görsel alanlarını optimize eder.

    optimize_images = {"alan_adi": maksimum_piksel}
    """

    optimize_images = {}

    def _optimize_uploaded_images(self):
        for name, max_px in self.optimize_images.items():
            f = getattr(self, name, None)
            if f and not getattr(f, "_committed", True):
                optimize_image(f, max_px)

    def save(self, *args, **kwargs):
        self._optimize_uploaded_images()
        super().save(*args, **kwargs)


def split_lines(value):
    return [line.strip() for line in str(value or "").splitlines() if line.strip()]


def split_tags(value):
    return [t.strip() for t in re.split(r"[,\n]", str(value or "")) if t.strip()]
