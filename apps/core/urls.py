from django.contrib.sitemaps.views import sitemap
from django.urls import path

from . import views
from .sitemaps import SITEMAPS

app_name = "core"

# Not: config/urls.py içinde EN SON eklenir; <slug>/ her şeyi yakalar.
urlpatterns = [
    path("", views.home, name="home"),
    path("sitemap.xml", sitemap, {"sitemaps": SITEMAPS}, name="sitemap"),
    path("robots.txt", views.robots_txt, name="robots"),
    path("<slug:slug>/", views.page_detail, name="page"),
]
