from django.urls import path

from . import views

app_name = "panel"

urlpatterns = [
    path("", views.dashboard, name="dashboard"),
    path("giris/", views.login_view, name="login"),
    path("cikis/", views.logout_view, name="logout"),
    path("ayarlar/", views.site_settings, name="settings"),
    path("metinler/", views.snippets, name="snippets"),
    path("hesabim/", views.profile, name="profile"),
    path("editor/yukle/", views.editor_upload, name="editor_upload"),
    # Sayfa oluşturucu
    path("sayfalar/yeni/", views.page_create, name="page_create"),
    path("sayfalar/<int:pk>/", views.page_builder, name="page_builder"),
    path("sayfalar/<int:pk>/bolum-ekle/", views.section_add, name="section_add"),
    path("sayfalar/<int:pk>/bolum-sirala/", views.sections_reorder, name="sections_reorder"),
    path("bolumler/<int:pk>/", views.section_edit, name="section_edit"),
    path("bolumler/<int:pk>/sil/", views.section_delete, name="section_delete"),
    path("bolumler/<int:pk>/kopyala/", views.section_duplicate, name="section_duplicate"),
    path("bolumler/<int:pk>/durum/", views.section_toggle, name="section_toggle"),
    # Mesajlar
    path("mesajlar/<int:pk>/", views.message_detail, name="message_detail"),
    # Kullanıcılar
    path("kullanicilar/", views.user_list, name="users"),
    path("kullanicilar/yeni/", views.user_form, name="user_create"),
    path("kullanicilar/<int:pk>/", views.user_form, name="user_edit"),
    path("kullanicilar/<int:pk>/sil/", views.user_delete, name="user_delete"),
    # Genel kaynaklar
    path("<slug:key>/", views.resource_list, name="list"),
    path("<slug:key>/yeni/", views.resource_form, name="create"),
    path("<slug:key>/sirala/", views.resource_reorder, name="reorder"),
    path("<slug:key>/toplu/", views.resource_bulk, name="bulk"),
    path("<slug:key>/yukle/", views.resource_bulk_upload, name="bulk_upload"),
    path("<slug:key>/disa-aktar/", views.resource_export, name="export"),
    path("<slug:key>/<int:pk>/", views.resource_form, name="edit"),
    path("<slug:key>/<int:pk>/sil/", views.resource_delete, name="delete"),
    path("<slug:key>/<int:pk>/degistir/<slug:field>/", views.resource_toggle, name="toggle"),
]
