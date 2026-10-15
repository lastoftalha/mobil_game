from django.conf import settings
from django.urls import include, path, re_path
from django.views.static import serve

from apps.contact import views as contact_views

urlpatterns = [
    path("panel/", include("apps.panel.urls")),
    path("bulten/", contact_views.subscribe, name="newsletter_subscribe"),
    path("", include("apps.content.urls")),
    path("", include("apps.blog.urls")),
]

if settings.SERVE_MEDIA:
    urlpatterns += [
        re_path(r"^%s(?P<path>.*)$" % settings.MEDIA_URL.lstrip("/"), serve, {"document_root": settings.MEDIA_ROOT}),
    ]

# Dinamik sayfalar en sonda (her şeyi yakalayan <slug>/ içerir)
urlpatterns += [path("", include("apps.core.urls"))]

handler404 = "apps.core.views.error_404"
handler500 = "apps.core.views.error_500"
