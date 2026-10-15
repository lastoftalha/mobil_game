import json
from urllib.parse import quote

from django import template
from django.template.loader import render_to_string
from django.utils.safestring import mark_safe

from apps.core import utils
from apps.core.snippets import DEFAULTS

register = template.Library()


def _snippets(context):
    request = context.get("request")
    cache = getattr(request, "_snippets", None) if request is not None else None
    if cache is None:
        from apps.core.models import TextSnippet

        cache = dict(TextSnippet.objects.values_list("key", "value"))
        if request is not None:
            request._snippets = cache
    return cache


@register.simple_tag(takes_context=True)
def t(context, key):
    """Panelden düzenlenebilen sabit metin."""
    value = _snippets(context).get(key)
    if value is None:
        value = DEFAULTS.get(key, key)
    return value


@register.filter
def fancy(value):
    return utils.fancy(value)


@register.filter
def plain(value):
    return utils.plain(value)


@register.filter
def tr_upper(value):
    return utils.tr_upper(value)


@register.filter
def lines(value):
    return utils.split_lines(value)


@register.filter
def pad2(value):
    try:
        return f"{int(value):02d}"
    except (TypeError, ValueError):
        return value


@register.filter
def repeat(value, times):
    try:
        return [value] * int(times)
    except (TypeError, ValueError):
        return [value]


@register.filter
def urlq(value):
    return quote(str(value or ""), safe="")


@register.filter
def year_fmt(value, year):
    return str(value or "").replace("{yil}", str(year))


@register.simple_tag(takes_context=True)
def render_section(context, section):
    from apps.core.section_data import build_section_context

    ctx = context.flatten()
    ctx.update(build_section_context(section, context))
    return mark_safe(render_to_string(f"site/sections/{section.type}.html", ctx, request=context.get("request")))


@register.simple_tag(takes_context=True)
def absolute(context, url):
    request = context.get("request")
    if not url:
        return ""
    if request is None or str(url).startswith("http"):
        return url
    return request.build_absolute_uri(url)


@register.simple_tag(takes_context=True)
def organization_jsonld(context):
    site = context.get("site")
    request = context.get("request")
    if site is None or request is None:
        return ""
    data = {
        "@context": "https://schema.org",
        "@type": "ProfessionalService",
        "name": site.site_name,
        "url": request.build_absolute_uri("/"),
    }
    if site.logo:
        data["logo"] = request.build_absolute_uri(site.logo.url)
    if site.phone:
        data["telephone"] = site.phone
    if site.email:
        data["email"] = site.email
    offices = list(context.get("offices") or [])
    if offices:
        data["address"] = {"@type": "PostalAddress", "streetAddress": offices[0].address, "addressCountry": "TR"}
    socials = [s.url for s in (context.get("socials") or [])]
    if socials:
        data["sameAs"] = socials
    payload = json.dumps(data, ensure_ascii=False).replace("</", "<\\/")
    return mark_safe(f'<script type="application/ld+json">{payload}</script>')


@register.filter
def nav_active(path, url):
    """Menü bağlantısı mevcut sayfaya ait mi?"""
    url = str(url or "")
    if not url.startswith("/"):
        return False
    if url == "/":
        return path == "/"
    return str(path).startswith(url)


@register.simple_tag(takes_context=True)
def logo_url(context, kind="logo"):
    """Panelden yüklenen logo yoksa varsayılan statik logoya düşer."""
    from django.templatetags.static import static

    site = context.get("site")
    defaults = {
        "logo": "site/img/logo-yellow.png",
        "logo_footer": "site/img/logo-yellow.png",
        "logo_dark": "site/img/logo-black.png",
        "logo_mark": "site/img/mark-yellow.png",
        "favicon": "site/img/favicon-512.png",
    }
    field = getattr(site, kind, None) if site else None
    if field:
        return field.url
    return static(defaults.get(kind, defaults["logo"]))
