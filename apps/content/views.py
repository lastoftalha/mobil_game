from django.shortcuts import get_object_or_404, render
from django.urls import reverse

from apps.core.utils import plain

from .models import Project, Service


def _visible(request, qs):
    if request.user.is_authenticated and request.user.is_staff:
        return qs
    return qs.filter(is_active=True)


def service_detail(request, slug):
    service = get_object_or_404(
        _visible(request, Service.objects.prefetch_related("features", "offerings", "steps")), slug=slug
    )
    context = {
        "service": service,
        "faqs": service.faqs.filter(is_active=True),
        "related_projects": service.projects.filter(is_active=True)[:4],
        "other_services": Service.objects.filter(is_active=True).exclude(pk=service.pk),
        "meta_title": plain(service.meta_title or service.title),
        "meta_description": service.meta_description or service.short_description,
        "meta_image": service.image.url if service.image else "",
        "body_class": "page-service",
        "panel_edit_url": reverse("panel:edit", args=["hizmetler", service.pk]),
    }
    return render(request, "site/service_detail.html", context)


def project_detail(request, slug):
    project = get_object_or_404(
        _visible(request, Project.objects.select_related("category").prefetch_related("images", "services")),
        slug=slug,
    )
    projects = list(Project.objects.filter(is_active=True).values_list("pk", flat=True))
    next_project = None
    if project.pk in projects and len(projects) > 1:
        idx = projects.index(project.pk)
        next_project = Project.objects.get(pk=projects[(idx + 1) % len(projects)])
    context = {
        "project": project,
        "next_project": next_project,
        "meta_title": plain(project.meta_title or project.title),
        "meta_description": project.meta_description or project.summary,
        "meta_image": project.cover.url if project.cover else "",
        "body_class": "page-project",
        "panel_edit_url": reverse("panel:edit", args=["portfoy", project.pk]),
    }
    return render(request, "site/project_detail.html", context)
