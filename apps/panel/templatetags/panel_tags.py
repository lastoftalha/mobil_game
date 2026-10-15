from django import forms, template
from django.db import models
from django.urls import reverse
from django.utils import timezone
from django.utils.html import format_html, strip_tags
from django.utils.text import Truncator

from apps.panel.widgets import CheckboxListWidget, ImageWidget, RichTextWidget, SwitchWidget, VideoWidget

register = template.Library()


@register.simple_tag
def edit_url(res, obj):
    if res.edit_url_name == "panel:edit":
        return reverse("panel:edit", args=[res.key, obj.pk])
    return reverse(res.edit_url_name, args=[obj.pk])


@register.simple_tag
def toggle_url(res, obj, field):
    return reverse("panel:toggle", args=[res.key, obj.pk, field])


@register.simple_tag
def render_cell(res, obj, name, is_first_text=False):
    if name == "__str__":
        return str(obj)
    field = obj._meta.get_field(name)
    value = getattr(obj, name)
    if isinstance(field, models.ImageField):
        if value:
            return format_html('<img class="thumb" src="{}" alt="" loading="lazy">', value.url)
        return format_html('<span class="thumb thumb--empty"><svg class="ico"><use href="#i-image"/></svg></span>')
    if isinstance(field, models.BooleanField):
        if name in res.toggle_fields:
            return format_html(
                '<button type="button" class="switch-btn{}" data-toggle-url="{}" aria-pressed="{}" '
                'aria-label="{}"><span></span></button>',
                " is-on" if value else "", toggle_url(res, obj, name), "true" if value else "false", field.verbose_name,
            )
        icon = "check" if value else "minus"
        return format_html('<svg class="ico bool-{}"><use href="#i-{}"/></svg>', "yes" if value else "no", icon)
    if name == "system_key":
        if value:
            return format_html('<span class="badge badge--brand">Sistem · {}</span>', obj.get_system_key_display())
        return format_html('<span class="badge">Özel sayfa</span>')
    if field.choices:
        display = getattr(obj, f"get_{name}_display")()
        css = "badge"
        if name == "status":
            css += " badge--ok" if value == "published" else " badge--muted"
        return format_html('<span class="{}">{}</span>', css, display)
    if value is None or value == "":
        return format_html('<span class="muted">—</span>')
    if isinstance(field, models.DateTimeField):
        return timezone.localtime(value).strftime("%d.%m.%Y %H:%M")
    if isinstance(field, models.SlugField):
        return format_html('<code>/{}/</code>', value)
    text = Truncator(strip_tags(str(value))).chars(70)
    return text


@register.filter
def widget_type(bound_field):
    widget = bound_field.field.widget
    if isinstance(widget, SwitchWidget):
        return "switch"
    if isinstance(widget, (ImageWidget, VideoWidget)):
        return "file"
    if isinstance(widget, RichTextWidget):
        return "rich"
    if isinstance(widget, CheckboxListWidget):
        return "checks"
    if isinstance(widget, forms.HiddenInput):
        return "hidden"
    return "text"


@register.filter
def is_wide(bound_field):
    widget = bound_field.field.widget
    return isinstance(widget, (forms.Textarea, RichTextWidget, ImageWidget, VideoWidget, CheckboxListWidget))


@register.filter
def get_item(mapping, key):
    try:
        return mapping.get(key)
    except AttributeError:
        return None


@register.simple_tag(takes_context=True)
def nav_active(context, *prefixes):
    path = context["request"].path
    for p in prefixes:
        if p == "/panel/" and path == "/panel/":
            return "is-active"
        if p != "/panel/" and path.startswith(p):
            return "is-active"
    return ""
