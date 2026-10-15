from django.utils import timezone

from .models import NavItem, Office, SiteSettings, SocialLink


class _Lazy:
    """İlk erişimde değerlendirilen sorgu (panel sayfalarında gereksiz sorgu olmasın)."""

    def __init__(self, fn):
        self._fn = fn
        self._value = None
        self._done = False

    def _get(self):
        if not self._done:
            self._value = self._fn()
            self._done = True
        return self._value

    def __iter__(self):
        return iter(self._get())

    def __len__(self):
        return len(self._get())

    def __bool__(self):
        return bool(self._get())

    def __getitem__(self, index):
        return self._get()[index]


def get_site_settings(request):
    cached = getattr(request, "_site_settings", None)
    if cached is None:
        cached = SiteSettings.load()
        request._site_settings = cached
    return cached


def site(request):
    s = get_site_settings(request)

    def nav(location):
        return _Lazy(lambda: list(NavItem.objects.filter(location=location, is_active=True)))

    def footer_services():
        from apps.content.models import Service

        return list(Service.objects.filter(is_active=True).only("title", "slug")[:8])

    return {
        "site": s,
        "header_nav": nav("header"),
        "footer_nav": nav("footer"),
        "socials": _Lazy(lambda: list(SocialLink.objects.filter(is_active=True))),
        "offices": _Lazy(lambda: list(Office.objects.filter(is_active=True))),
        "footer_services": _Lazy(footer_services),
        "current_year": timezone.localdate().year,
    }
