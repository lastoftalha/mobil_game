from django import forms
from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password
from django.db import models

from apps.core.models import Page, Section, SiteSettings
from apps.core.sections import SECTION_TYPES, TITLE_HELP

from .widgets import CheckboxListWidget, CodeWidget, ColorWidget, ImageWidget, RichTextWidget, SwitchWidget, VideoWidget

TEXTAREA_SHORT = {"rows": 3}
FANCY_FIELDS = {"title", "subtitle"}


class OrderField(forms.IntegerField):
    """Alt öğelerdeki gizli sıra alanı; boş gelirse 0 kabul edilir."""

    def __init__(self, **kwargs):
        kwargs.update(required=False, min_value=0, widget=forms.HiddenInput(attrs={"data-order": "1"}))
        super().__init__(**kwargs)

    def clean(self, value):
        return super().clean(value) or 0


def make_formfield_callback(rich_fields=(), code_fields=(), fancy_fields=()):
    """Model alanlarını panel widget'larıyla eşleştirir."""

    def callback(field, **kwargs):
        if field.name == "order":
            return OrderField(label=field.verbose_name, initial=0)
        if isinstance(field, models.ImageField):
            kwargs["widget"] = ImageWidget
        elif isinstance(field, models.FileField):
            kwargs["widget"] = VideoWidget
        elif isinstance(field, models.BooleanField):
            kwargs["widget"] = SwitchWidget
        elif isinstance(field, models.ManyToManyField):
            kwargs["widget"] = CheckboxListWidget
        elif field.name in rich_fields:
            kwargs["widget"] = RichTextWidget
        elif field.name in code_fields:
            kwargs["widget"] = CodeWidget
        elif isinstance(field, models.DateTimeField):
            kwargs["widget"] = forms.DateTimeInput(attrs={"type": "datetime-local", "class": "input"},
                                                   format="%Y-%m-%dT%H:%M")
        elif isinstance(field, models.CharField) and (field.name.endswith("color") or field.name.startswith("color_")):
            kwargs["widget"] = ColorWidget
        elif isinstance(field, models.TextField):
            rows = 3 if field.name in ("title", "subtitle", "short_description", "excerpt", "summary",
                                       "meta_description", "address", "quote", "intro", "answer", "text") else 6
            kwargs["widget"] = forms.Textarea(attrs={"rows": rows, "class": "input"})
        formfield = field.formfield(**kwargs)
        if formfield is None:
            return None
        if field.name in fancy_fields:
            formfield.help_text = (formfield.help_text + " " if formfield.help_text else "") + TITLE_HELP
        widget = formfield.widget
        if not isinstance(widget, (ImageWidget, VideoWidget, SwitchWidget, RichTextWidget, ColorWidget,
                                   CheckboxListWidget, forms.CheckboxInput)):
            css = widget.attrs.get("class", "")
            if "input" not in css:
                widget.attrs["class"] = (css + " input").strip()
        if isinstance(field, models.SlugField):
            widget.attrs["data-slug"] = "1"
        return formfield

    return callback


# ----------------------------------------------------------------------------- sayfa / bölüm
class PageForm(forms.ModelForm):
    class Meta:
        model = Page
        fields = ["title", "slug", "is_published", "show_in_sitemap", "meta_title", "meta_description", "og_image"]
        widgets = {
            "title": forms.TextInput(attrs={"class": "input", "data-slug-source": "1"}),
            "slug": forms.TextInput(attrs={"class": "input", "data-slug": "1"}),
            "is_published": SwitchWidget,
            "show_in_sitemap": SwitchWidget,
            "meta_title": forms.TextInput(attrs={"class": "input", "data-counter": "60"}),
            "meta_description": forms.Textarea(attrs={"class": "input", "rows": 3, "data-counter": "160"}),
            "og_image": ImageWidget,
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["slug"].required = False
        if self.instance.pk and self.instance.is_system:
            self.fields["slug"].disabled = True
            self.fields["slug"].help_text = "Sistem sayfalarının adresi değiştirilemez."
        if self.instance.pk and self.instance.is_home:
            self.fields["is_published"].disabled = True

    def clean_slug(self):
        from apps.core.utils import tr_slugify

        slug = self.cleaned_data.get("slug")
        if self.instance.pk and self.instance.is_system:
            return self.instance.slug
        slug = tr_slugify(slug or self.cleaned_data.get("title") or "")
        if not slug:
            raise forms.ValidationError("Geçerli bir adres girin.")
        reserved = {"panel", "media", "static", "bulten", "sitemap-xml", "robots-txt", "anasayfa"}
        if slug in reserved:
            raise forms.ValidationError("Bu adres sistem tarafından kullanılıyor.")
        if Page.objects.filter(slug=slug).exclude(pk=self.instance.pk).exists():
            raise forms.ValidationError("Bu adresle başka bir sayfa var.")
        return slug


def section_form_class(section_type):
    cfg = SECTION_TYPES[section_type]
    fields = ["name", "theme", "anchor", "is_active"] + list(cfg["fields"])
    labels = dict(cfg.get("labels", {}))
    callback = make_formfield_callback(rich_fields=("body",), fancy_fields=FANCY_FIELDS & set(cfg["fields"]))

    class SectionForm(forms.ModelForm):
        def __init__(self, *args, **kwargs):
            super().__init__(*args, **kwargs)
            for name, label in labels.items():
                if name in self.fields:
                    self.fields[name].label = label
            if "theme" in self.fields:
                default = cfg.get("theme", "dark")
                choices = [("", f"Varsayılan ({dict(self.fields['theme'].choices).get(default, default)})")]
                choices += [c for c in self.fields["theme"].choices if c[0]]
                self.fields["theme"].choices = choices
            if "subtitle" in self.fields and section_type in ("hero_home", "marquee_text"):
                self.fields["subtitle"].widget.attrs["rows"] = 6
                self.fields["subtitle"].help_text = "Her satıra bir öğe yazın."

    return forms.models.modelform_factory(Section, form=SectionForm, fields=fields, formfield_callback=callback)


# ----------------------------------------------------------------------------- site ayarları
SETTINGS_TABS = [
    ("genel", "Genel", ["site_name", "tagline", "header_cta_text", "header_cta_url", "footer_tagline",
                        "footer_about", "copyright_text", "newsletter_enabled"]),
    ("logolar", "Logolar", ["logo", "logo_footer", "logo_dark", "logo_mark", "favicon"]),
    ("renkler", "Renkler", ["color_primary", "color_dark", "color_gray", "color_light"]),
    ("iletisim", "İletişim", ["email", "email_secondary", "phone", "phone_secondary", "whatsapp",
                              "show_whatsapp_button", "notify_email", "contact_success_message"]),
    ("seo", "SEO", ["meta_title", "meta_title_suffix", "meta_description", "meta_keywords", "og_image"]),
    ("cerez", "Çerez bandı", ["cookie_banner_enabled", "cookie_text", "cookie_policy_url"]),
    ("kodlar", "Özel kodlar", ["head_code", "body_end_code"]),
]


def settings_form_class(user):
    tabs = [t for t in SETTINGS_TABS if t[0] != "kodlar" or user.is_superuser]
    fields = [f for _, _, fs in tabs for f in fs]
    callback = make_formfield_callback(code_fields=("head_code", "body_end_code"))
    form_class = forms.models.modelform_factory(SiteSettings, fields=fields, formfield_callback=callback)
    return form_class, tabs


# ----------------------------------------------------------------------------- kullanıcılar
User = get_user_model()


class UserForm(forms.ModelForm):
    password1 = forms.CharField(label="Şifre", required=False, strip=False,
                                widget=forms.PasswordInput(attrs={"class": "input", "autocomplete": "new-password"}))
    password2 = forms.CharField(label="Şifre (tekrar)", required=False, strip=False,
                                widget=forms.PasswordInput(attrs={"class": "input", "autocomplete": "new-password"}))

    class Meta:
        model = User
        fields = ["username", "first_name", "last_name", "email", "is_active", "is_superuser"]
        labels = {"is_superuser": "Tam yetkili yönetici", "is_active": "Aktif"}
        help_texts = {
            "is_superuser": "Kullanıcıları ve özel kodları yönetebilir.",
            "username": "Giriş için kullanılır.",
        }
        widgets = {
            "username": forms.TextInput(attrs={"class": "input", "autocomplete": "off"}),
            "first_name": forms.TextInput(attrs={"class": "input"}),
            "last_name": forms.TextInput(attrs={"class": "input"}),
            "email": forms.EmailInput(attrs={"class": "input"}),
            "is_active": SwitchWidget,
            "is_superuser": SwitchWidget,
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if not self.instance.pk:
            self.fields["password1"].required = True
            self.fields["password2"].required = True
        else:
            self.fields["password1"].help_text = "Değiştirmek istemiyorsanız boş bırakın."

    def clean(self):
        cleaned = super().clean()
        p1, p2 = cleaned.get("password1"), cleaned.get("password2")
        if p1 or p2:
            if p1 != p2:
                self.add_error("password2", "Şifreler eşleşmiyor.")
            else:
                try:
                    validate_password(p1, self.instance)
                except forms.ValidationError as exc:
                    self.add_error("password1", exc)
        return cleaned

    def save(self, commit=True):
        user = super().save(commit=False)
        user.is_staff = True
        if self.cleaned_data.get("password1"):
            user.set_password(self.cleaned_data["password1"])
        if commit:
            user.save()
        return user


class ProfileForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ["first_name", "last_name", "email"]
        widgets = {
            "first_name": forms.TextInput(attrs={"class": "input"}),
            "last_name": forms.TextInput(attrs={"class": "input"}),
            "email": forms.EmailInput(attrs={"class": "input"}),
        }


class MessageNoteForm(forms.Form):
    note = forms.CharField(label="İç not", required=False, widget=forms.Textarea(attrs={"rows": 4, "class": "input"}))
