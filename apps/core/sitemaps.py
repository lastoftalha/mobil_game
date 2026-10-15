from django.contrib.sitemaps import Sitemap

from apps.blog.models import Post
from apps.content.models import Project, Service

from .models import Page


class PageSitemap(Sitemap):
    changefreq = "weekly"

    def items(self):
        return Page.objects.filter(is_published=True, show_in_sitemap=True)

    def lastmod(self, obj):
        return obj.updated_at

    def priority(self, obj):
        return 1.0 if obj.is_home else 0.8


class ServiceSitemap(Sitemap):
    changefreq = "monthly"
    priority = 0.8

    def items(self):
        return Service.objects.filter(is_active=True)

    def lastmod(self, obj):
        return obj.updated_at


class ProjectSitemap(Sitemap):
    changefreq = "monthly"
    priority = 0.6

    def items(self):
        return Project.objects.filter(is_active=True)

    def lastmod(self, obj):
        return obj.updated_at


class PostSitemap(Sitemap):
    changefreq = "weekly"
    priority = 0.6

    def items(self):
        return Post.objects.published()

    def lastmod(self, obj):
        return obj.updated_at


SITEMAPS = {"pages": PageSitemap, "services": ServiceSitemap, "projects": ProjectSitemap, "posts": PostSitemap}
