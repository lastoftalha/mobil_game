import shutil
import tempfile

from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.core.management import call_command
from django.test import TestCase, override_settings

from apps.contact.models import ContactMessage, Subscriber
from apps.core.models import Page, Section, SiteSettings, TextSnippet
from apps.core.utils import fancy, tr_slugify

TEMP_MEDIA = tempfile.mkdtemp(prefix="test-media-")


class UtilsTests(TestCase):
    def test_tr_slugify(self):
        self.assertEqual(tr_slugify("Sosyal Medya Yönetimi"), "sosyal-medya-yonetimi")
        self.assertEqual(tr_slugify("İŞ ÇIĞLIK Ğ"), "is-ciglik-g")

    def test_fancy_markup_is_escaped(self):
        html = fancy("Merhaba [dünya] {zarif}\n<script>alert(1)</script>")
        self.assertIn('<mark class="hl">dünya</mark>', html)
        self.assertIn('<em class="serif">zarif</em>', html)
        self.assertIn("<br>", html)
        self.assertNotIn("<script>", html)


@override_settings(MEDIA_ROOT=TEMP_MEDIA, ALLOWED_HOSTS=["testserver"])
class PublicSiteTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        call_command("seed_site", verbosity=0)

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(TEMP_MEDIA, ignore_errors=True)

    def setUp(self):
        cache.clear()

    def test_all_public_pages_render(self):
        urls = ["/", "/hakkimizda/", "/hizmetler/", "/portfoy/", "/galeri/", "/referanslar/", "/blog/", "/iletisim/",
                "/hizmetler/sosyal-medya-yonetimi/", "/portfoy/model-cekimleri/", "/blog/dijital-reklamciligin-gelecegi/",
                "/blog/?kategori=sosyal-medya", "/blog/?q=reklam", "/sitemap.xml", "/robots.txt"]
        for url in urls:
            with self.subTest(url=url):
                self.assertEqual(self.client.get(url).status_code, 200)

    def test_home_content_is_dynamic(self):
        response = self.client.get("/")
        self.assertContains(response, "bize bırakılır")
        hero = Section.objects.get(type="hero_home")
        hero.title = "Yeni [başlık]"
        hero.save()
        response = self.client.get("/")
        self.assertContains(response, '<mark class="hl">başlık</mark>', html=False)

    def test_inactive_section_hidden(self):
        Section.objects.filter(type="statement").update(is_active=False)
        self.assertNotContains(self.client.get("/"), "statement__title")

    def test_unknown_and_unpublished_pages_404(self):
        self.assertEqual(self.client.get("/yok-boyle-bir-sayfa/").status_code, 404)
        self.assertEqual(self.client.get("/kvkk/").status_code, 404)
        staff = get_user_model().objects.create_user("editor", password="x-Pass-12345", is_staff=True)
        self.client.force_login(staff)
        self.assertEqual(self.client.get("/kvkk/").status_code, 200)

    def test_home_slug_redirects_to_root(self):
        response = self.client.get("/anasayfa/")
        self.assertRedirects(response, "/", status_code=301)

    def test_snippet_override(self):
        TextSnippet.objects.create(key="form.gonder", value="Hemen Gönder")
        self.assertContains(self.client.get("/iletisim/"), "Hemen Gönder")

    def test_settings_colors_applied(self):
        s = SiteSettings.load()
        s.color_primary = "#FF0000"
        s.save()
        self.assertContains(self.client.get("/"), "--c-primary:#FF0000")

    def test_contact_form_success(self):
        data = {"name": "Ayşe Yılmaz", "email": "ayse@example.com", "phone": "", "company": "",
                "service": "Web Tasarım", "message": "Merhaba, web sitesi istiyoruz.", "consent": "on"}
        response = self.client.post("/iletisim/", data)
        self.assertEqual(response.status_code, 302)
        msg = ContactMessage.objects.get()
        self.assertEqual(msg.service, "Web Tasarım")
        self.assertFalse(msg.is_read)

    def test_contact_form_errors(self):
        response = self.client.post("/iletisim/", {"name": "", "email": "yanlis", "message": ""})
        self.assertEqual(response.status_code, 400)
        self.assertEqual(ContactMessage.objects.count(), 0)
        self.assertContains(response, "field__error", status_code=400)

    def test_contact_honeypot(self):
        data = {"name": "Bot", "email": "bot@example.com", "message": "spam", "consent": "on", "website": "http://spam"}
        self.client.post("/iletisim/", data)
        self.assertEqual(ContactMessage.objects.count(), 0)

    def test_post_to_page_without_form_is_404(self):
        self.assertEqual(self.client.post("/hakkimizda/", {}).status_code, 404)

    def test_newsletter(self):
        self.client.post("/bulten/", {"email": "Abone@Example.com", "next": "/"})
        self.client.post("/bulten/", {"email": "abone@example.com", "next": "/"})
        self.assertEqual(Subscriber.objects.count(), 1)
        response = self.client.post("/bulten/", {"email": "x", "next": "https://evil.example/"})
        self.assertTrue(response["Location"].startswith("/"))

    def test_post_view_counter(self):
        from apps.blog.models import Post

        url = "/blog/dijital-reklamciligin-gelecegi/"
        self.client.get(url)
        self.client.get(url)
        self.assertEqual(Post.objects.get(slug="dijital-reklamciligin-gelecegi").views, 1)

    def test_seed_is_idempotent(self):
        pages = Page.objects.count()
        call_command("seed_site", verbosity=0)
        self.assertEqual(Page.objects.count(), pages)
