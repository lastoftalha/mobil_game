from django.urls import path

from . import views

app_name = "content"

urlpatterns = [
    path("hizmetler/<slug:slug>/", views.service_detail, name="service_detail"),
    path("portfoy/<slug:slug>/", views.project_detail, name="project_detail"),
]
