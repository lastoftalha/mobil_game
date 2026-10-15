import json
import shutil
import tempfile
from io import BytesIO

from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.core.files.uploadedfile import SimpleUploadedFile
from django.core.management import call_command
from django.test import TestCase, override_settings
from PIL import Image

from apps.content.models import FAQ, GalleryImage, Service
from apps.core.models import Page, Section, SectionItem, SiteSettings, TextSnippet
from apps.panel.registry import REGISTRY

TEMP_MEDIA = tempfile.mkdtemp(prefix="test-panel-media-")
User = get_user_model()


def image_file(name="test.png", size=(40, 30)):
    buf = BytesIO()
    Image.new("RGB", size, (246, 197, 0)).save(buf, "PNG")
    return SimpleUploadedFile(name, buf.getvalue(), content_type="image/png")


def management(prefix, total=0, initial=0):
    return {f"{prefix}-TOTAL_FORMS": str(total), f"{prefix}-INITIAL_FORMS": str(initial),
            f"{prefix}-MIN_NUM_FORMS": "0", f"{prefix}-MAX_NUM_FORMS": "1000"}


@override_settings(MEDIA_ROOT=TEMP_MEDIA, ALLOWED_HOSTS=["testserver"])
class PanelTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        call_command("seed_site", verbosity=0)
        cls.admin = User.objects.create_superuser("admin", "admin@example.com", "Guclu-Sifre-2026")
        cls.editor = User.objects.create_user("editor", "editor@example.com", "Guclu-Sifre-2026", is_staff=True)

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(TEMP_MEDIA, ignore_errors=True)

    def setUp(self):
        cache.clear()
        self.client.force_login(self.admin)

    # ---------------------------------------------------------------- erişim
    def test_anonymous_redirected_to_login(self):
        self.client.logout()
        response = self.client.get("/panel/hizmetler/")
        self.assertRedirects(response, "/panel/giris/?next=/panel/hizmetler/")

    def test_non_staff_cannot_login(self):
        self.client.logout()
        User.objects.create_user("musteri", password="Guclu-Sifre-2026")
        self.client.post("/panel/giris/", {"username": "musteri", "password": "Guclu-Sifre-2026"})
        self.assertEqual(self.client.get("/panel/").status_code, 302)

    def test_login_and_throttle(self):
        self.client.logout()
        response = self.client.post("/panel/giris/?next=/panel/ayarlar/", {"username": "admin", "password": "Guclu-Sifre-2026", "next": "/panel/ayarlar/"})
        self.assertRedirects(response, "/panel/ayarlar/")
        self.client.logout()
        for _ in range(8):
            self.client.post("/panel/giris/", {"username": "admin", "password": "yanlis"})
        response = self.client.post("/panel/giris/", {"username": "admin", "password": "Guclu-Sifre-2026"})
        self.assertEqual(response.status_code, 200)  # kilitli: giriş yapılmadı

    def test_editor_cannot_manage_users_or_codes(self):
        self.client.force_login(self.editor)
        self.assertEqual(self.client.get("/panel/kullanicilar/").status_code, 403)
        response = self.client.get("/panel/ayarlar/")
        self.assertNotContains(response, "head_code")

    def test_every_panel_screen_renders(self):
        urls = ["/panel/", "/panel/ayarlar/", "/panel/metinler/", "/panel/hesabim/", "/panel/kullanicilar/",
                "/panel/kullanicilar/yeni/", "/panel/sayfalar/yeni/"]
        for key, res in REGISTRY.items():
            urls.append(f"/panel/{key}/")
            if res.can_create and key != "sayfalar":
                urls.append(f"/panel/{key}/yeni/")
            obj = res.model.objects.first()
            if obj and key not in ("sayfalar", "mesajlar"):
                urls += [f"/panel/{key}/{obj.pk}/", f"/panel/{key}/{obj.pk}/sil/"]
        for page in Page.objects.all():
            urls.append(f"/panel/sayfalar/{page.pk}/")
        for section in Section.objects.all():
            urls.append(f"/panel/bolumler/{section.pk}/")
        for url in urls:
            with self.subTest(url=url):
                self.assertEqual(self.client.get(url).status_code, 200)

    # ---------------------------------------------------------------- genel CRUD
    def test_create_service_with_inlines(self):
        data = {
            "title": "Marka Danışmanlığı", "slug": "", "short_description": "Kısa", "tags": "a, b",
            "is_active": "on", "show_on_home": "on", "intro": "Giriş", "overview": "<p>Detay</p>",
            "meta_title": "", "meta_description": "",
            **management("servicefeature", 2), **management("serviceoffering"), **management("servicestep"),
            **management("faq", 1),
            "servicefeature-0-title": "Özellik 1", "servicefeature-0-text": "x", "servicefeature-0-order": "1",
            "servicefeature-1-title": "Özellik 0", "servicefeature-1-text": "y", "servicefeature-1-order": "0",
            "faq-0-question": "Soru?", "faq-0-answer": "Cevap", "faq-0-is_active": "on",
        }
        response = self.client.post("/panel/hizmetler/yeni/", data)
        service = Service.objects.get(title="Marka Danışmanlığı")
        self.assertRedirects(response, f"/panel/hizmetler/{service.pk}/")
        self.assertEqual(service.slug, "marka-danismanligi")
        self.assertEqual([f.title for f in service.features.all()], ["Özellik 0", "Özellik 1"])
        self.assertEqual(FAQ.objects.get(question="Soru?").service, service)
        self.assertEqual(self.client.get(service.get_absolute_url()).status_code, 200)

    def test_invalid_form_shows_errors(self):
        data = {"title": "", **management("servicefeature"), **management("serviceoffering"),
                **management("servicestep"), **management("faq")}
        response = self.client.post("/panel/hizmetler/yeni/", data)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "field__error")

    def test_toggle_and_reorder(self):
        service = Service.objects.first()
        response = self.client.post(f"/panel/hizmetler/{service.pk}/degistir/is_active/")
        self.assertEqual(response.json(), {"ok": True, "value": False})
        self.assertEqual(self.client.post(f"/panel/hizmetler/{service.pk}/degistir/title/").status_code, 404)
        ids = list(Service.objects.values_list("pk", flat=True))[::-1]
        self.client.post("/panel/hizmetler/sirala/", json.dumps({"ids": ids, "offset": 0}), content_type="application/json")
        self.assertEqual(list(Service.objects.values_list("pk", flat=True)), ids)

    def test_bulk_upload_gallery(self):
        before = GalleryImage.objects.count()
        response = self.client.post("/panel/galeri/yukle/", {"files": [image_file("a.png"), image_file("b-gorsel.png")]})
        self.assertRedirects(response, "/panel/galeri/")
        self.assertEqual(GalleryImage.objects.count(), before + 2)

    def test_bulk_upload_rejects_non_images(self):
        before = GalleryImage.objects.count()
        bad = SimpleUploadedFile("x.png", b"not an image", content_type="image/png")
        self.client.post("/panel/galeri/yukle/", {"files": [bad]})
        self.assertEqual(GalleryImage.objects.count(), before)

    def test_bulk_delete_skips_system_pages(self):
        ids = list(Page.objects.values_list("pk", flat=True))
        self.client.post("/panel/sayfalar/toplu/", {"action": "delete", "ids": ids})
        self.assertEqual(Page.objects.filter(system_key__isnull=False).count(), 8)
        self.assertFalse(Page.objects.filter(slug="kvkk").exists())

    def test_system_page_cannot_be_deleted(self):
        home = Page.objects.get(system_key="home")
        self.client.post(f"/panel/sayfalar/{home.pk}/sil/")
        self.assertTrue(Page.objects.filter(pk=home.pk).exists())

    def test_csv_export(self):
        response = self.client.get("/panel/mesajlar/disa-aktar/")
        self.assertEqual(response.status_code, 200)
        self.assertIn("text/csv", response["Content-Type"])

    # ---------------------------------------------------------------- sayfa oluşturucu
    def test_page_create_and_sections(self):
        response = self.client.post("/panel/sayfalar/yeni/", {"title": "Kariyer Fırsatları", "slug": "",
                                                               "is_published": "on", "show_in_sitemap": "on"})
        page = Page.objects.get(title="Kariyer Fırsatları")
        self.assertRedirects(response, f"/panel/sayfalar/{page.pk}/")
        self.assertEqual(page.slug, "kariyer-firsatlari")
        self.assertEqual(page.sections.count(), 1)

        response = self.client.post(f"/panel/sayfalar/{page.pk}/bolum-ekle/", {"type": "stats"})
        section = page.sections.get(type="stats")
        self.assertRedirects(response, f"/panel/bolumler/{section.pk}/")

        data = {"name": "", "theme": "", "anchor": "", "is_active": "on", "eyebrow": "Biz", "title": "Rakamlar",
                **management("items", 2),
                "items-0-value": "10+", "items-0-title": "Yıl", "items-0-text": "", "items-0-is_active": "on", "items-0-order": "0",
                "items-1-value": "", "items-1-title": "", "items-1-text": "", "items-1-order": "1", "items-1-DELETE": "on"}
        response = self.client.post(f"/panel/bolumler/{section.pk}/", data)
        self.assertRedirects(response, f"/panel/bolumler/{section.pk}/")
        self.assertEqual(SectionItem.objects.filter(section=section).count(), 1)
        self.assertContains(self.client.get("/kariyer-firsatlari/"), "10+")

        self.client.post(f"/panel/bolumler/{section.pk}/kopyala/")
        self.assertEqual(page.sections.filter(type="stats").count(), 2)
        copy = page.sections.filter(type="stats").exclude(pk=section.pk).get()
        self.assertEqual(copy.items.count(), 1)

        ids = list(page.sections.values_list("pk", flat=True))[::-1]
        self.client.post(f"/panel/sayfalar/{page.pk}/bolum-sirala/", json.dumps({"ids": ids}), content_type="application/json")
        self.assertEqual(list(page.sections.values_list("pk", flat=True)), ids)

        self.assertEqual(self.client.post(f"/panel/bolumler/{copy.pk}/durum/").json()["value"], False)
        self.client.post(f"/panel/bolumler/{copy.pk}/sil/")
        self.assertFalse(Section.objects.filter(pk=copy.pk).exists())

    def test_reserved_and_system_slugs(self):
        response = self.client.post("/panel/sayfalar/yeni/", {"title": "Panel", "slug": "panel"})
        self.assertEqual(response.status_code, 200)
        self.assertFalse(Page.objects.filter(slug="panel").exists())
        about = Page.objects.get(system_key="about")
        self.client.post(f"/panel/sayfalar/{about.pk}/", {"title": "Biz Kimiz", "slug": "baska", "is_published": "on"})
        about.refresh_from_db()
        self.assertEqual((about.title, about.slug), ("Biz Kimiz", "hakkimizda"))

    # ---------------------------------------------------------------- ayarlar / metinler
    def test_settings_save(self):
        response = self.client.get("/panel/ayarlar/")
        form = response.context["form"]
        data = {}
        for name, field in form.fields.items():
            value = form.initial.get(name)
            if isinstance(value, bool):
                if value:
                    data[name] = "on"
            elif value is not None and not hasattr(value, "url"):
                data[name] = value
        data["site_name"] = "Yeni Ajans Adı"
        data["color_primary"] = "#00AAFF"
        response = self.client.post("/panel/ayarlar/", data)
        self.assertEqual(response.status_code, 302)
        settings_obj = SiteSettings.load()
        self.assertEqual(settings_obj.site_name, "Yeni Ajans Adı")
        self.assertTrue(settings_obj.logo)  # dokunulmayan görsel korunur

    def test_snippets_save_and_reset(self):
        self.client.post("/panel/metinler/", {"s__form.gonder": "Gönder Gitsin", "s__genel.tumu": "Tümü"})
        self.assertEqual(TextSnippet.objects.get(key="form.gonder").value, "Gönder Gitsin")
        self.assertFalse(TextSnippet.objects.filter(key="genel.tumu").exists())
        self.client.post("/panel/metinler/", {"s__form.gonder": ""})
        self.assertFalse(TextSnippet.objects.filter(key="form.gonder").exists())

    # ---------------------------------------------------------------- kullanıcılar / yükleme
    def test_user_management(self):
        response = self.client.post("/panel/kullanicilar/yeni/", {
            "username": "yeni", "first_name": "Yeni", "last_name": "Kişi", "email": "yeni@example.com",
            "is_active": "on", "password1": "Cok-Guclu-Sifre-99", "password2": "Cok-Guclu-Sifre-99",
        })
        self.assertRedirects(response, "/panel/kullanicilar/")
        user = User.objects.get(username="yeni")
        self.assertTrue(user.is_staff and not user.is_superuser)
        self.client.post(f"/panel/kullanicilar/{self.admin.pk}/sil/")
        self.assertTrue(User.objects.filter(pk=self.admin.pk).exists())

    def test_editor_image_upload(self):
        response = self.client.post("/panel/editor/yukle/", {"file": image_file("x.png", (3000, 2000))})
        payload = response.json()
        self.assertTrue(payload["ok"])
        self.assertTrue(payload["url"].startswith("/media/editor/"))
        bad = self.client.post("/panel/editor/yukle/", {"file": SimpleUploadedFile("x.svg", b"<svg/>")})
        self.assertEqual(bad.status_code, 400)

    def test_message_detail_marks_read(self):
        from apps.contact.models import ContactMessage

        msg = ContactMessage.objects.create(name="Ali", email="ali@example.com", message="Merhaba")
        self.client.get(f"/panel/mesajlar/{msg.pk}/")
        msg.refresh_from_db()
        self.assertTrue(msg.is_read)
