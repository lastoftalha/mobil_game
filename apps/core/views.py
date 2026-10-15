from django.contrib import messages
from django.http import Http404, HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.views.decorators.http import require_GET

from .context_processors import get_site_settings
from .models import Page, TextSnippet
from .snippets import DEFAULTS


def _snippet(key):
    obj = TextSnippet.objects.filter(key=key).first()
    return obj.value if obj else DEFAULTS.get(key, key)


def _visible_page_qs(request):
    qs = Page.objects.all()
    if not (request.user.is_authenticated and request.user.is_staff):
        qs = qs.filter(is_published=True)
    return qs


def render_page(request, page, extra=None, status=200):
    sections = page.sections.filter(is_active=True).prefetch_related("items")
    context = {
        "page": page,
        "sections": sections,
        "meta_title": page.seo_title,
        "meta_description": page.meta_description,
        "meta_image": page.og_image.url if page.og_image else "",
        "body_class": f"page-{page.system_key or 'custom'}",
        "panel_edit_url": reverse("panel:page_builder", args=[page.pk]),
    }
    if extra:
        context.update(extra)
    return render(request, "site/page.html", context, status=status)


def home(request):
    page = _visible_page_qs(request).filter(system_key="home").first()
    if page is None:
        return render(request, "site/setup.html", status=200)
    return render_page(request, page)


def page_detail(request, slug):
    page = get_object_or_404(_visible_page_qs(request), slug=slug)
    if page.is_home:
        return redirect("core:home", permanent=True)
    if request.method == "POST":
        if page.sections.filter(type="contact_form", is_active=True).exists():
            return _handle_contact(request, page)
        raise Http404
    return render_page(request, page)


def _handle_contact(request, page):
    from apps.contact.forms import ContactForm
    from apps.contact.services import client_ip, notify_new_message, rate_limited
    from apps.content.models import Service

    site = get_site_settings(request)
    form = ContactForm(request.POST, services=Service.objects.filter(is_active=True))
    target = f"{page.get_absolute_url()}#iletisim-formu"
    if form.is_bot():
        messages.success(request, site.contact_success_message)
        return redirect(target)
    if rate_limited(request, "contact"):
        messages.error(request, _snippet("form.cok_hizli"))
        return render_page(request, page, {"contact_form": form}, status=429)
    if form.is_valid():
        msg = form.save(commit=False)
        msg.ip_address = client_ip(request)
        msg.page_url = request.path[:300]
        msg.save()
        notify_new_message(site, msg)
        messages.success(request, site.contact_success_message)
        return redirect(target)
    messages.error(request, _snippet("form.hata"))
    return render_page(request, page, {"contact_form": form}, status=400)


@require_GET
def robots_txt(request):
    lines = [
        "User-agent: *",
        "Disallow: /panel/",
        f"Sitemap: {request.build_absolute_uri(reverse('core:sitemap'))}",
    ]
    return HttpResponse("\n".join(lines) + "\n", content_type="text/plain")


def error_404(request, exception=None):
    return render(request, "site/error.html", {"code": 404, "meta_title": "404"}, status=404)


def error_500(request):
    # 500 sırasında veritabanına erişim sorunlu olabilir; sade şablon kullan
    return render(request, "500.html", status=500)
