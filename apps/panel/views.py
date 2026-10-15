import csv
import json
import uuid
from functools import wraps
from pathlib import Path

from django import forms
from django.contrib import messages
from django.contrib.auth import get_user_model, login, logout, update_session_auth_hash
from django.contrib.auth.forms import AuthenticationForm, PasswordChangeForm
from django.contrib.auth.views import redirect_to_login
from django.core.cache import cache
from django.core.exceptions import PermissionDenied
from django.core.files.base import ContentFile
from django.core.files.storage import default_storage
from django.core.paginator import Paginator
from django.db import models, transaction
from django.db.models import Max, Q
from django.forms import HiddenInput, inlineformset_factory, modelform_factory
from django.http import Http404, HttpResponse, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils import timezone
from django.utils.http import url_has_allowed_host_and_scheme
from django.views.decorators.http import require_POST

from apps.blog.models import Post
from apps.contact.models import ContactMessage, Subscriber
from apps.contact.services import client_ip
from apps.content.models import GalleryImage, Project, Service
from apps.core.models import Page, Section, SectionItem, SiteSettings, TextSnippet
from apps.core.sections import SECTION_TYPES
from apps.core.snippets import DEFAULTS, group_of
from apps.core.utils import optimized_content

from .forms import (
    MessageNoteForm, PageForm, ProfileForm, UserForm, make_formfield_callback, section_form_class,
    settings_form_class,
)
from .registry import REGISTRY, grouped_registry

User = get_user_model()

LOGIN_LIMIT = 8
LOGIN_WINDOW = 15 * 60


# ----------------------------------------------------------------------------- yetki
def staff_required(view):
    @wraps(view)
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect_to_login(request.get_full_path(), reverse("panel:login"))
        if not (request.user.is_active and request.user.is_staff):
            raise PermissionDenied
        return view(request, *args, **kwargs)

    return wrapper


def superuser_required(view):
    @wraps(view)
    @staff_required
    def wrapper(request, *args, **kwargs):
        if not request.user.is_superuser:
            raise PermissionDenied
        return view(request, *args, **kwargs)

    return wrapper


def get_resource(request, key):
    res = REGISTRY.get(key)
    if res is None:
        raise Http404
    if res.superuser_only and not request.user.is_superuser:
        raise PermissionDenied
    return res


def render_panel(request, template, context=None, status=200):
    ctx = {
        "nav_groups": grouped_registry(request.user),
        "unread_count": ContactMessage.objects.filter(is_read=False).count(),
        "site": SiteSettings.load(),
    }
    ctx.update(context or {})
    return render(request, template, ctx, status=status)


def _safe_next(request, fallback):
    target = request.POST.get("next") or request.GET.get("next")
    if target and url_has_allowed_host_and_scheme(target, allowed_hosts={request.get_host()},
                                                  require_https=request.is_secure()):
        return target
    return fallback


def _next_order(model, **filters):
    value = model.objects.filter(**filters).aggregate(m=Max("order"))["m"]
    return 0 if value is None else value + 1


# ----------------------------------------------------------------------------- giriş / çıkış
def login_view(request):
    if request.user.is_authenticated and request.user.is_staff:
        return redirect(_safe_next(request, reverse("panel:dashboard")))
    key = f"panel-login:{client_ip(request)}"
    attempts = cache.get(key, 0)
    form = AuthenticationForm(request, data=request.POST or None)
    form.fields["username"].widget.attrs.update({"class": "input", "autofocus": True, "placeholder": "Kullanıcı adı"})
    form.fields["password"].widget.attrs.update({"class": "input", "placeholder": "Şifre"})
    if request.method == "POST":
        if attempts >= LOGIN_LIMIT:
            messages.error(request, "Çok fazla hatalı deneme yapıldı. Lütfen 15 dakika sonra tekrar deneyin.")
        elif form.is_valid():
            user = form.get_user()
            if user.is_staff:
                login(request, user)
                cache.delete(key)
                return redirect(_safe_next(request, reverse("panel:dashboard")))
            cache.set(key, attempts + 1, LOGIN_WINDOW)
            messages.error(request, "Bu hesabın panele erişim yetkisi yok.")
        else:
            cache.set(key, attempts + 1, LOGIN_WINDOW)
    return render(request, "panel/login.html", {"form": form, "next": request.GET.get("next", ""),
                                                "site": SiteSettings.load()})


@require_POST
def logout_view(request):
    logout(request)
    messages.success(request, "Güvenli şekilde çıkış yaptınız.")
    return redirect("panel:login")


# ----------------------------------------------------------------------------- panel ana sayfa
@staff_required
def dashboard(request):
    stats = [
        ("Sayfalar", Page.objects.count(), "files", reverse("panel:list", args=["sayfalar"])),
        ("Hizmetler", Service.objects.filter(is_active=True).count(), "briefcase", reverse("panel:list", args=["hizmetler"])),
        ("Projeler", Project.objects.filter(is_active=True).count(), "folder-kanban", reverse("panel:list", args=["portfoy"])),
        ("Blog yazıları", Post.objects.published().count(), "newspaper", reverse("panel:list", args=["blog"])),
        ("Galeri", GalleryImage.objects.filter(is_active=True).count(), "images", reverse("panel:list", args=["galeri"])),
        ("Bülten aboneleri", Subscriber.objects.filter(is_active=True).count(), "at-sign", reverse("panel:list", args=["aboneler"])),
    ]
    home = Page.objects.filter(system_key="home").first()
    context = {
        "stats": stats,
        "recent_messages": ContactMessage.objects.all()[:6],
        "top_posts": Post.objects.order_by("-views")[:5],
        "recent_posts": Post.objects.all()[:5],
        "home_page": home,
        "pages": Page.objects.all()[:12],
        "now": timezone.localtime(),
    }
    return render_panel(request, "panel/dashboard.html", context)


# ----------------------------------------------------------------------------- genel liste
def _filter_defs(request, res, qs):
    defs = []
    for name in res.list_filters:
        field = res.model._meta.get_field(name)
        value = request.GET.get(name, "")
        if field.is_relation:
            options = [(str(o.pk), str(o)) for o in field.related_model.objects.all()]
            if field.null:
                options.append(("__none__", "— Boş"))
            if value == "__none__":
                qs = qs.filter(**{f"{name}__isnull": True})
            elif value:
                qs = qs.filter(**{f"{name}_id": value})
        elif isinstance(field, models.BooleanField):
            options = [("1", "Evet"), ("0", "Hayır")]
            if value in ("1", "0"):
                qs = qs.filter(**{name: value == "1"})
        else:
            options = [(str(k), str(v)) for k, v in field.choices]
            if value:
                qs = qs.filter(**{name: value})
        defs.append({"name": name, "label": field.verbose_name, "options": options, "value": value})
    return defs, qs


@staff_required
def resource_list(request, key):
    res = get_resource(request, key)
    qs = res.model.objects.all()
    if res.select_related:
        qs = qs.select_related(*res.select_related)
    query = request.GET.get("q", "").strip()
    if query and res.search_fields:
        cond = Q()
        for f in res.search_fields:
            cond |= Q(**{f"{f}__icontains": query})
        qs = qs.filter(cond)
    filters, qs = _filter_defs(request, res, qs)
    is_filtered = bool(query or any(f["value"] for f in filters))
    can_sort = res.sortable and not is_filtered
    per_page = 500 if can_sort else res.per_page
    paginator = Paginator(qs, per_page)
    page_obj = paginator.get_page(request.GET.get("sayfa"))
    params = request.GET.copy()
    params.pop("sayfa", None)
    bulk_extras = []
    for name in res.bulk_upload_extra:
        field = res.model._meta.get_field(name)
        bulk_extras.append({"name": name, "label": field.verbose_name,
                            "options": [(o.pk, str(o)) for o in field.related_model.objects.all()]})
    context = {
        "res": res,
        "page_obj": page_obj,
        "objects": page_obj.object_list,
        "query": query,
        "filters": filters,
        "is_filtered": is_filtered,
        "can_sort": can_sort,
        "order_offset": (page_obj.number - 1) * per_page,
        "querystring": params.urlencode(),
        "bulk_extras": bulk_extras,
        "main_col": next((name for name, label in res.list_display if label), res.list_display[0][0]),
    }
    return render_panel(request, "panel/list.html", context)


# ----------------------------------------------------------------------------- genel form
def _build_formsets(res, obj, request):
    formsets = []
    for inline in res.inlines:
        fields = list(inline.fields) + (["order"] if inline.sortable else [])
        widgets = {"order": HiddenInput(attrs={"data-order": "1"})} if inline.sortable else {}
        fs_class = inlineformset_factory(
            res.model, inline.model, fk_name=inline.fk_name, fields=fields, extra=0, can_delete=True,
            formfield_callback=make_formfield_callback(rich_fields=inline.rich_fields), widgets=widgets,
        )
        data = request.POST if request.method == "POST" else None
        files = request.FILES if request.method == "POST" else None
        fs = fs_class(data, files, instance=obj, prefix=inline.prefix)
        fs.inline = inline
        formsets.append(fs)
    return formsets


def _save_bulk_inline_files(request, formsets, obj):
    created = 0
    for fs in formsets:
        inline = fs.inline
        if not inline.bulk_field:
            continue
        fk = fs.fk.name
        for upload in request.FILES.getlist(f"bulk-{inline.prefix}"):
            try:
                forms.ImageField().clean(upload)
            except forms.ValidationError:
                messages.warning(request, f"{upload.name} geçerli bir görsel değil, atlandı.")
                continue
            item = inline.model(**{fk: obj})
            setattr(item, inline.bulk_field, upload)
            if inline.sortable:
                item.order = _next_order(inline.model, **{fk: obj})
            item.save()
            created += 1
    return created


@staff_required
def resource_form(request, key, pk=None):
    res = get_resource(request, key)
    if res.key == "sayfalar":
        return redirect("panel:page_builder", pk=pk) if pk else redirect("panel:page_create")
    if pk is None and not res.can_create:
        raise Http404
    obj = get_object_or_404(res.model, pk=pk) if pk else res.model()
    form_class = modelform_factory(
        res.model, fields=res.form_fields,
        formfield_callback=make_formfield_callback(rich_fields=res.rich_fields, fancy_fields=res.fancy_fields),
    )
    form = form_class(request.POST or None, request.FILES or None, instance=obj)
    for name in ("meta_title",):
        if name in form.fields:
            form.fields[name].widget.attrs["data-counter"] = "60"
    if "meta_description" in form.fields:
        form.fields["meta_description"].widget.attrs["data-counter"] = "160"
    if "slug" in form.fields:
        form.fields["slug"].required = False
        form.fields["slug"].help_text = "Boş bırakılırsa başlıktan otomatik oluşturulur."
    for source in ("title", "name"):
        if source in form.fields and "slug" in form.fields:
            form.fields[source].widget.attrs["data-slug-source"] = "1"
            break
    formsets = _build_formsets(res, obj, request)

    if request.method == "POST":
        if form.is_valid() and all(fs.is_valid() for fs in formsets):
            with transaction.atomic():
                is_new = form.instance.pk is None
                if is_new and res.sortable:
                    form.instance.order = _next_order(res.model)
                obj = form.save()
                for fs in formsets:
                    fs.instance = obj
                    fs.save()
                added = _save_bulk_inline_files(request, formsets, obj)
            msg = f"“{obj}” kaydedildi."
            if added:
                msg += f" {added} görsel eklendi."
            messages.success(request, msg)
            if "_addanother" in request.POST:
                return redirect("panel:create", key=key)
            if "_list" in request.POST:
                return redirect("panel:list", key=key)
            return redirect("panel:edit", key=key, pk=obj.pk)
        messages.error(request, "Kaydedilemedi. Lütfen işaretli alanları kontrol edin.")

    tabs = []
    for title, names in res.fieldsets:
        bound = [form[n] for n in names if n in form.fields]
        tabs.append({"title": title, "fields": bound,
                     "has_errors": any(b.errors for b in bound)})
    context = {
        "res": res,
        "obj": obj,
        "form": form,
        "tabs": tabs,
        "formsets": formsets,
        "is_new": obj.pk is None,
        "view_url": obj.get_absolute_url() if obj.pk and hasattr(obj, "get_absolute_url") else "",
    }
    return render_panel(request, "panel/form.html", context)


@staff_required
def resource_delete(request, key, pk):
    res = get_resource(request, key)
    if not res.can_delete:
        raise Http404
    obj = get_object_or_404(res.model, pk=pk)
    if isinstance(obj, Page) and obj.is_system:
        messages.error(request, "Sistem sayfaları silinemez; yayından kaldırabilirsiniz.")
        return redirect("panel:page_builder", pk=obj.pk)
    if request.method == "POST":
        name = str(obj)
        obj.delete()
        messages.success(request, f"“{name}” silindi.")
        return redirect("panel:list", key=key)
    related = []
    for rel in obj._meta.related_objects:
        accessor = rel.get_accessor_name()
        if rel.on_delete == models.CASCADE and hasattr(obj, accessor):
            try:
                count = getattr(obj, accessor).count()
            except Exception:
                count = 0
            if count:
                related.append(f"{count} {rel.related_model._meta.verbose_name_plural}")
    return render_panel(request, "panel/confirm_delete.html", {"res": res, "obj": obj, "related": related})


@staff_required
@require_POST
def resource_toggle(request, key, pk, field):
    res = get_resource(request, key)
    if field not in res.toggle_fields:
        raise Http404
    obj = get_object_or_404(res.model, pk=pk)
    if isinstance(obj, Page) and obj.is_home and field == "is_published":
        return JsonResponse({"ok": False, "error": "Ana sayfa yayından kaldırılamaz."}, status=400)
    setattr(obj, field, not getattr(obj, field))
    obj.save(update_fields=[field])
    return JsonResponse({"ok": True, "value": getattr(obj, field)})


@staff_required
@require_POST
def resource_reorder(request, key):
    res = get_resource(request, key)
    if not res.sortable:
        raise Http404
    try:
        payload = json.loads(request.body or "{}")
        ids = [int(i) for i in payload.get("ids", [])]
        offset = int(payload.get("offset", 0))
    except (ValueError, TypeError):
        return JsonResponse({"ok": False}, status=400)
    with transaction.atomic():
        for index, pk in enumerate(ids):
            res.model.objects.filter(pk=pk).update(order=offset + index)
    return JsonResponse({"ok": True})


@staff_required
@require_POST
def resource_bulk(request, key):
    res = get_resource(request, key)
    ids = [int(i) for i in request.POST.getlist("ids") if i.isdigit()]
    action = request.POST.get("action")
    qs = res.model.objects.filter(pk__in=ids)
    if not ids:
        messages.warning(request, "Önce kayıt seçin.")
    elif action == "delete" and res.can_delete:
        if res.model is Page:
            qs = qs.filter(system_key__isnull=True)
        count = qs.count()
        for obj in qs:
            obj.delete()
        messages.success(request, f"{count} kayıt silindi.")
    elif action in ("activate", "deactivate"):
        field = next((f for f in ("is_active", "is_published", "is_read") if f in res.toggle_fields), None)
        if field:
            count = qs.update(**{field: action == "activate"})
            messages.success(request, f"{count} kayıt güncellendi.")
    return redirect(_safe_next(request, reverse("panel:list", args=[key])))


@staff_required
@require_POST
def resource_bulk_upload(request, key):
    res = get_resource(request, key)
    if not res.bulk_upload_field:
        raise Http404
    extras = {}
    for name in res.bulk_upload_extra:
        value = request.POST.get(name)
        if value:
            field = res.model._meta.get_field(name)
            extras[name] = field.related_model.objects.filter(pk=value).first()
    created = 0
    for upload in request.FILES.getlist("files"):
        try:
            forms.ImageField().clean(upload)
        except forms.ValidationError:
            messages.warning(request, f"{upload.name} geçerli bir görsel değil, atlandı.")
            continue
        obj = res.model(**extras)
        setattr(obj, res.bulk_upload_field, upload)
        label = Path(upload.name).stem.replace("-", " ").replace("_", " ").strip()[:100]
        for attr in ("name", "title"):
            if hasattr(obj, attr) and not getattr(obj, attr):
                setattr(obj, attr, label.title() if attr == "name" else label)
                break
        if res.sortable:
            obj.order = _next_order(res.model)
        obj.save()
        created += 1
    if created:
        messages.success(request, f"{created} görsel yüklendi.")
    return redirect("panel:list", key=key)


@staff_required
def resource_export(request, key):
    res = get_resource(request, key)
    if not res.export_csv:
        raise Http404
    response = HttpResponse(content_type="text/csv; charset=utf-8")
    response["Content-Disposition"] = f'attachment; filename="{key}-{timezone.localdate():%Y%m%d}.csv"'
    response.write("﻿")
    writer = csv.writer(response, delimiter=";")
    fields = [f for f in res.model._meta.fields if f.name not in ("id",)]
    writer.writerow([f.verbose_name for f in fields])
    for obj in res.model.objects.all():
        row = []
        for f in fields:
            value = getattr(obj, f.name)
            if hasattr(value, "strftime"):
                value = timezone.localtime(value).strftime("%d.%m.%Y %H:%M") if timezone.is_aware(value) else value
            text = str(value)
            if text[:1] in ("=", "+", "-", "@"):
                text = "'" + text  # CSV formül enjeksiyonuna karşı
            row.append(text)
        writer.writerow(row)
    return response


# ----------------------------------------------------------------------------- sayfa oluşturucu
@staff_required
def page_create(request):
    form = PageForm(request.POST or None, request.FILES or None)
    if request.method == "POST" and form.is_valid():
        page = form.save()
        Section.objects.create(page=page, type="page_hero", title=page.title, order=0)
        messages.success(request, "Sayfa oluşturuldu. Şimdi bölümlerini ekleyebilirsiniz.")
        return redirect("panel:page_builder", pk=page.pk)
    return render_panel(request, "panel/page_create.html", {"form": form, "res": REGISTRY["sayfalar"]})


@staff_required
def page_builder(request, pk):
    page = get_object_or_404(Page, pk=pk)
    form = PageForm(request.POST or None, request.FILES or None, instance=page)
    if request.method == "POST":
        if form.is_valid():
            form.save()
            messages.success(request, "Sayfa ayarları kaydedildi.")
            return redirect("panel:page_builder", pk=page.pk)
        messages.error(request, "Sayfa ayarları kaydedilemedi.")
    sections = page.sections.all().prefetch_related("items")
    types = [{"key": k, **v} for k, v in SECTION_TYPES.items()]
    return render_panel(request, "panel/page_builder.html", {
        "page": page, "form": form, "sections": sections, "section_types": types, "res": REGISTRY["sayfalar"],
    })


@staff_required
@require_POST
def section_add(request, pk):
    page = get_object_or_404(Page, pk=pk)
    section_type = request.POST.get("type")
    if section_type not in SECTION_TYPES:
        raise Http404
    section = Section.objects.create(page=page, type=section_type, order=_next_order(Section, page=page))
    messages.success(request, f"“{section.type_label}” bölümü eklendi.")
    return redirect("panel:section_edit", pk=section.pk)


@staff_required
def section_edit(request, pk):
    section = get_object_or_404(Section.objects.select_related("page"), pk=pk)
    cfg = SECTION_TYPES.get(section.type)
    if cfg is None:
        raise Http404
    form_class = section_form_class(section.type)
    form = form_class(request.POST or None, request.FILES or None, instance=section)
    formset = None
    item_cfg = cfg.get("items")
    if item_cfg:
        item_fields = list(item_cfg["fields"]) + ["is_active", "order"]
        fs_class = inlineformset_factory(
            Section, SectionItem, fields=item_fields, extra=0, can_delete=True,
            formfield_callback=make_formfield_callback(), widgets={"order": HiddenInput(attrs={"data-order": "1"})},
        )
        formset = fs_class(request.POST or None, request.FILES or None, instance=section, prefix="items")
        for f in list(formset.forms) + [formset.empty_form]:
            for name, label in item_cfg.get("labels", {}).items():
                if name in f.fields:
                    f.fields[name].label = label
            if "text" in f.fields:
                f.fields["text"].widget.attrs["rows"] = 3
    if request.method == "POST":
        if form.is_valid() and (formset is None or formset.is_valid()):
            with transaction.atomic():
                form.save()
                if formset is not None:
                    formset.save()
                    for upload in request.FILES.getlist("bulk-items"):
                        try:
                            forms.ImageField().clean(upload)
                        except forms.ValidationError:
                            continue
                        item = SectionItem(section=section, order=_next_order(SectionItem, section=section))
                        item.image = upload
                        item.save()
            messages.success(request, "Bölüm kaydedildi.")
            if "_back" in request.POST:
                return redirect(f"{reverse('panel:page_builder', args=[section.page_id])}#bolum-{section.pk}")
            return redirect("panel:section_edit", pk=section.pk)
        messages.error(request, "Kaydedilemedi. Lütfen işaretli alanları kontrol edin.")
    return render_panel(request, "panel/section_form.html", {
        "section": section, "page": section.page, "cfg": cfg, "form": form, "formset": formset,
        "res": REGISTRY["sayfalar"], "item_cfg": item_cfg,
        "has_image_items": bool(item_cfg and "image" in item_cfg["fields"]),
    })


@staff_required
@require_POST
def section_delete(request, pk):
    section = get_object_or_404(Section, pk=pk)
    page_id = section.page_id
    section.delete()
    messages.success(request, "Bölüm silindi.")
    return redirect("panel:page_builder", pk=page_id)


@staff_required
@require_POST
def section_duplicate(request, pk):
    section = get_object_or_404(Section, pk=pk)
    items = list(section.items.all())
    with transaction.atomic():
        Section.objects.filter(page=section.page, order__gt=section.order).update(order=models.F("order") + 1)
        section.pk = None
        section.id = None
        section.order += 1
        section.name = (section.name or section.type_label) + " (kopya)"
        section.save()
        for item in items:
            item.pk = None
            item.id = None
            item.section = section
            item.save()
    messages.success(request, "Bölüm kopyalandı.")
    return redirect(f"{reverse('panel:page_builder', args=[section.page_id])}#bolum-{section.pk}")


@staff_required
@require_POST
def section_toggle(request, pk):
    section = get_object_or_404(Section, pk=pk)
    section.is_active = not section.is_active
    section.save(update_fields=["is_active"])
    return JsonResponse({"ok": True, "value": section.is_active})


@staff_required
@require_POST
def sections_reorder(request, pk):
    page = get_object_or_404(Page, pk=pk)
    try:
        ids = [int(i) for i in json.loads(request.body or "{}").get("ids", [])]
    except (ValueError, TypeError):
        return JsonResponse({"ok": False}, status=400)
    with transaction.atomic():
        for index, sid in enumerate(ids):
            Section.objects.filter(pk=sid, page=page).update(order=index)
    return JsonResponse({"ok": True})


# ----------------------------------------------------------------------------- site ayarları / metinler
@staff_required
def site_settings(request):
    obj = SiteSettings.load()
    form_class, tabs = settings_form_class(request.user)
    form = form_class(request.POST or None, request.FILES or None, instance=obj)
    if request.method == "POST":
        if form.is_valid():
            form.save()
            messages.success(request, "Site ayarları kaydedildi.")
            tab = request.POST.get("_tab", "")
            return redirect(reverse("panel:settings") + (f"#{tab}" if tab else ""))
        messages.error(request, "Kaydedilemedi. Lütfen işaretli alanları kontrol edin.")
    tab_list = []
    for key, title, names in tabs:
        bound = [form[n] for n in names if n in form.fields]
        tab_list.append({"key": key, "title": title, "fields": bound, "has_errors": any(b.errors for b in bound)})
    return render_panel(request, "panel/settings.html", {"form": form, "tabs": tab_list})


@staff_required
def snippets(request):
    stored = {s.key: s for s in TextSnippet.objects.all()}
    if request.method == "POST":
        changed = 0
        for key, default in DEFAULTS.items():
            field = f"s__{key}"
            if field not in request.POST:
                continue
            value = request.POST.get(field, "").strip()
            current = stored.get(key)
            if not value or value == default:
                if current:
                    current.delete()
                    changed += 1
                continue
            if current is None:
                TextSnippet.objects.create(key=key, value=value)
                changed += 1
            elif current.value != value:
                current.value = value
                current.save(update_fields=["value", "updated_at"])
                changed += 1
        messages.success(request, f"Sabit metinler kaydedildi ({changed} değişiklik).")
        return redirect("panel:snippets")
    groups = {}
    for key, default in DEFAULTS.items():
        current = stored.get(key)
        groups.setdefault(group_of(key), []).append({
            "key": key, "field": f"s__{key}", "default": default,
            "value": current.value if current else default, "custom": current is not None,
            "long": len(default) > 70,
        })
    return render_panel(request, "panel/snippets.html", {"groups": groups})


# ----------------------------------------------------------------------------- mesajlar
@staff_required
def message_detail(request, pk):
    msg = get_object_or_404(ContactMessage, pk=pk)
    if not msg.is_read:
        msg.is_read = True
        msg.save(update_fields=["is_read"])
    form = MessageNoteForm(request.POST or None, initial={"note": msg.note})
    if request.method == "POST":
        if "_unread" in request.POST:
            msg.is_read = False
            msg.save(update_fields=["is_read"])
            messages.success(request, "Mesaj okunmadı olarak işaretlendi.")
            return redirect("panel:list", key="mesajlar")
        if form.is_valid():
            msg.note = form.cleaned_data["note"]
            msg.save(update_fields=["note"])
            messages.success(request, "Not kaydedildi.")
            return redirect("panel:message_detail", pk=msg.pk)
    nav = list(ContactMessage.objects.values_list("pk", flat=True))
    idx = nav.index(msg.pk) if msg.pk in nav else 0
    return render_panel(request, "panel/message_detail.html", {
        "msg": msg, "form": form, "res": REGISTRY["mesajlar"],
        "prev_id": nav[idx - 1] if idx > 0 else None,
        "next_id": nav[idx + 1] if idx + 1 < len(nav) else None,
    })


# ----------------------------------------------------------------------------- kullanıcılar / hesap
@superuser_required
def user_list(request):
    return render_panel(request, "panel/users.html", {"users": User.objects.filter(is_staff=True).order_by("username")})


@superuser_required
def user_form(request, pk=None):
    obj = get_object_or_404(User, pk=pk, is_staff=True) if pk else User(is_active=True)
    form = UserForm(request.POST or None, instance=obj)
    if request.method == "POST":
        if form.is_valid():
            if obj.pk == request.user.pk and (not form.cleaned_data["is_superuser"] or not form.cleaned_data["is_active"]):
                messages.error(request, "Kendi yönetici yetkinizi veya hesabınızı pasif yapamazsınız.")
            else:
                user = form.save()
                if user.pk == request.user.pk and form.cleaned_data.get("password1"):
                    update_session_auth_hash(request, user)
                messages.success(request, f"“{user.username}” kaydedildi.")
                return redirect("panel:users")
        else:
            messages.error(request, "Kaydedilemedi. Lütfen işaretli alanları kontrol edin.")
    return render_panel(request, "panel/user_form.html", {"form": form, "obj": obj, "is_new": obj.pk is None})


@superuser_required
@require_POST
def user_delete(request, pk):
    obj = get_object_or_404(User, pk=pk, is_staff=True)
    if obj.pk == request.user.pk:
        messages.error(request, "Kendi hesabınızı silemezsiniz.")
    else:
        obj.delete()
        messages.success(request, "Kullanıcı silindi.")
    return redirect("panel:users")


@staff_required
def profile(request):
    profile_form = ProfileForm(request.POST if "_profile" in request.POST else None, instance=request.user)
    password_form = PasswordChangeForm(request.user, request.POST if "_password" in request.POST else None)
    for f in password_form.fields.values():
        f.widget.attrs["class"] = "input"
    if request.method == "POST":
        if "_profile" in request.POST and profile_form.is_valid():
            profile_form.save()
            messages.success(request, "Bilgileriniz güncellendi.")
            return redirect("panel:profile")
        if "_password" in request.POST and password_form.is_valid():
            user = password_form.save()
            update_session_auth_hash(request, user)
            messages.success(request, "Şifreniz değiştirildi.")
            return redirect("panel:profile")
        messages.error(request, "Lütfen işaretli alanları kontrol edin.")
    return render_panel(request, "panel/profile.html", {"profile_form": profile_form, "password_form": password_form})


# ----------------------------------------------------------------------------- editör görsel yükleme
@staff_required
@require_POST
def editor_upload(request):
    upload = request.FILES.get("file")
    if not upload:
        return JsonResponse({"ok": False, "error": "Dosya bulunamadı."}, status=400)
    try:
        forms.ImageField().clean(upload)
    except forms.ValidationError:
        return JsonResponse({"ok": False, "error": "Geçerli bir görsel yükleyin."}, status=400)
    ext = Path(upload.name).suffix.lower()
    if ext not in (".jpg", ".jpeg", ".png", ".webp", ".gif"):
        return JsonResponse({"ok": False, "error": "Desteklenmeyen dosya türü."}, status=400)
    name = f"{uuid.uuid4().hex}{ext}"
    content = optimized_content(upload, name, 2000)
    if content is None:
        upload.seek(0)
        content = ContentFile(upload.read(), name=name)
    path = default_storage.save(f"editor/{timezone.now():%Y/%m}/{name}", content)
    return JsonResponse({"ok": True, "url": default_storage.url(path)})
