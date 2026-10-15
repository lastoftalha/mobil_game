"""Eski siteden (selim.bitasarimlazim.com) derlenen içeriklerle örnek verileri yükler.

Kullanım:
    python manage.py seed_site            # veritabanı boşsa yükler
    python manage.py seed_site --reset    # mevcut İÇERİKLERİ silip baştan yükler
                                          # (kullanıcılar, mesajlar ve aboneler korunur)
"""
import json
from datetime import timedelta
from pathlib import Path

from django.conf import settings
from django.core.files.base import ContentFile
from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils import timezone

from apps.blog.models import Category, Post
from apps.content.models import (
    FAQ, Brand, GalleryCategory, GalleryImage, Project, ProjectCategory, ProjectImage, Service,
    ServiceFeature, ServiceOffering, ServiceStep, Testimonial,
)
from apps.core.models import NavItem, Office, Page, Section, SectionItem, SiteSettings, SocialLink, TextSnippet

SEED_DIR = Path(settings.BASE_DIR) / "seed"


def media(rel):
    path = SEED_DIR / "media" / rel
    return ContentFile(path.read_bytes(), name=path.name)


# --------------------------------------------------------------------------- hizmetler
SERVICES = [
    {
        "title": "Sosyal Medya Yönetimi",
        "slug": "sosyal-medya-yonetimi",
        "image": "services/sosyal-medya-yonetimi.jpg",
        "tags": "Instagram, TikTok, Reels, İçerik Planı",
        "short": "Markanız için etkileşim sağlayan, dönüşüm odaklı ve sürdürülebilir dijital içerikler üretiyoruz.",
        "intro": "Markanız için etkileşim sağlayan, dönüşüm odaklı ve sürdürülebilir dijital içerikler üretiyoruz. Marka kimliğinizden strateji geliştirmeye, içerik üretiminden yönetim süreçlerine kadar uçtan uca çözümler sunarak sosyal medyada güçlü ve büyüyen bir marka varlığı oluşturmanıza yardımcı oluyoruz.",
        "overview": (
            "<p>Bitasarımlazım ekibi olarak, sosyal medya yönetimi alanında sunduğumuz profesyonel hizmetlerle markanızı dijital dünyada öne çıkarıyoruz. Sosyal medya, günümüz dijital çağında markaların bilinirliğini artırmak, müşterilerle etkileşime geçmek ve sadık bir müşteri kitlesi oluşturmak için kritik bir araçtır.</p>"
            "<h3>Sosyal Medya Stratejisi Geliştirme</h3><p>Her markanın kendine özgü bir sesi ve hedef kitlesi vardır. Markanızın hedef kitlesine uygun özel sosyal medya stratejileri geliştiriyor; doğru mesajı, doğru zamanda, doğru kitleye ulaştırmayı hedefliyoruz.</p>"
            "<h3>Etkileşim ve Müşteri İlişkileri Yönetimi</h3><p>Müşterilerle birebir etkileşimde bulunmak, sorularına hızlı yanıt vermek ve geri dönüşler almak müşteri memnuniyetini artırır. Sosyal medya hesaplarınızda müşterilerinizle etkin bir iletişim sağlıyor, markanızın güçlü bir imajla temsil edilmesini sağlıyoruz.</p>"
            "<h3>Reklam Yönetimi ve Hedefleme</h3><p>Google ve sosyal medya platformlarında markanızın potansiyel müşterilere ulaşmasını sağlayacak reklam kampanyaları düzenliyoruz. Reklamlar, hedef kitlenizin demografik özelliklerine ve ilgi alanlarına göre optimize edilerek maksimum geri dönüş sağlanır.</p>"
        ),
        "features": [
            ("Strateji Odaklı Yönetim", "Özel hedef ve rakip analizine dayalı sosyal medya stratejileri."),
            ("Markaya Uygun İçerik", "Dikkat çekici grafik tasarımlar, reels/video içerikleri ve kreatif metinler."),
            ("Performans Analizi", "Etkileşim, erişim ve dönüşüm verileri değerlendirilerek sürekli optimizasyon sağlanır."),
            ("Etkileşim ve Topluluk Yönetimi", "Yorum ve mesaj geri dönüşleri hızlı şekilde takip edilir, kullanıcılarla iletişim güçlendirilir."),
        ],
        "offerings": [
            ("Stratejik Planlama & Hedef Belirleme", "Marka ihtiyaç analizi\nRakip incelemesi\nHedef kitle tanımlaması\nİçerik yol haritası"),
            ("Profesyonel İçerik Takvimi", "Aylık planlanan içerikler\nÖzel temalar ve konsept günleri\nPaylaşım takvimi"),
            ("Tasarım & Kreatif İçerik Üretimi", "Markaya özel görsel tasarımlar\nReels / video içerikleri\nMotion grafikler\nHikâye tasarımları"),
        ],
        "steps": [
            ("İçerik Planlama", "Marka hedeflerine göre aylık içerik planı ve paylaşım takvimi hazırlanır."),
            ("Sipariş Oluşturma", "Onaylanan plan doğrultusunda tasarım ve metin üretimi başlar."),
            ("Video Çekimleri", "Reels ve tanıtım içerikleri için profesyonel çekimler yapılır."),
            ("Teslimat & Paylaşım", "İçerikler planlanan zamanda yayınlanır, performans raporlanır."),
        ],
        "faqs": [
            ("Sosyal medya yönetimi hangi platformları kapsıyor?", "Instagram, Facebook, TikTok, LinkedIn ve YouTube dahil olmak üzere markanızın hedef kitlesine uygun tüm platformlarda profesyonel içerik planlama, tasarım ve yönetim hizmeti sunuyoruz."),
            ("İçerikler tamamen markaya özel mi tasarlanıyor?", "Evet, tüm içerikler markanızın kurumsal kimliği, hedef kitlesi ve sektörel ihtiyaçları doğrultusunda özgün olarak hazırlanır. Tasarım dili, renk paleti ve iletişim tonu size özel belirlenir."),
            ("Sonuçları nasıl takip edebiliyoruz?", "Düzenli performans raporları ve analizleri ile erişim, etkileşim ve büyüme verilerini size sunuyor; süreci şeffaf şekilde ilerletiyoruz. Gerektiğinde stratejik optimizasyonlar sağlanır."),
        ],
    },
    {
        "title": "Tanıtım Filmi Çekimi",
        "slug": "tanitim-filmi-cekimi",
        "image": "services/tanitim-filmi-cekimi.jpg",
        "tags": "Video Tanıtım, Drone, Post Prodüksiyon",
        "short": "Markanızın değerini en iyi şekilde yansıtan profesyonel tanıtım filmleri ve post prodüksiyon hizmetleri.",
        "intro": "Markanızın değerini en iyi şekilde yansıtan profesyonel tanıtım filmleri ve post prodüksiyon hizmetleri sunuyoruz. Modern ekipmanlarımız, yaratıcı yaklaşımımız ve uzman ekibimizle markanızın hikâyesini en etkileyici şekilde anlatıyoruz.",
        "overview": (
            "<h3>Profesyonel Çekim Süreci</h3><p>Son teknoloji ekipmanlar ve deneyimli çekim ekibimizle yüksek kaliteli görüntüler elde ediyoruz. İç mekân, dış mekân ve drone çekimleri gibi farklı perspektifleri bir araya getirerek dinamik ve dikkat çekici videolar hazırlıyoruz.</p>"
            "<h3>Post Prodüksiyon</h3><p>Çekim sonrası videolarınızı mükemmelleştirmek için kapsamlı bir post prodüksiyon süreci yürütüyoruz. Renk düzenleme, ses miksajı, özel efektler, animasyon ve görsel geçişlerle videonuzun profesyonel görünmesini sağlıyoruz.</p>"
            "<h3>Drone ve Hava Çekimleri</h3><p>Markanızı havadan görüntülemek ve tanıtım filminize yenilikçi bir boyut kazandırmak için drone çekimleri gerçekleştiriyoruz.</p>"
            "<p>İşletmenizin vizyonunu yansıtan, izleyiciler üzerinde kalıcı bir etki bırakan içeriklerimizle hedeflerinize ulaşmanız için yanınızdayız.</p>"
        ),
        "features": [
            ("Yaratıcı ve Stratejik Konsept", "Markanızın hedefleri ve mesajı doğrultusunda özgün bir hikâye kurgusu."),
            ("Profesyonel Çekim Süreci", "Deneyimli ekip ve modern ekipmanlarla yüksek kaliteli görüntü ve ses."),
            ("Drone ve Hava Çekimleri", "Geniş alanları ve etkileyici perspektifleri yüksek çözünürlükle sunuyoruz."),
            ("Hikâye Anlatımı Odaklı Yaklaşım", "İzleyicide kalıcı etki bırakan, duygu odaklı kurgu."),
        ],
        "offerings": [],
        "steps": [
            ("İhtiyaç Analizi", "Markanızın hedefleri ve mesajı doğrultusunda tanıtım filminin konsepti ve ana temasını belirliyoruz."),
            ("Konsept Belirleme", "Film senaryosu hazırlanır, çekim mekânları ve ekip planlaması yapılır; prodüksiyon süreci organize edilir."),
            ("Çekim ve Prodüksiyon", "Profesyonel ekip ve ekipmanlarla çekimler gerçekleştirilir; yüksek kaliteli görüntü ve ses kaydı sağlanır."),
            ("Kurgu ve Teslimat", "Çekilen görüntüler profesyonel şekilde kurgulanır, son düzenlemeler yapılarak film teslim edilir."),
        ],
        "faqs": [
            ("Tanıtım filmi çekimi ne kadar sürer?", "Çekim süresi projenin kapsamına bağlıdır ancak genellikle konsept belirleme, çekim ve kurgu dahil olmak üzere 1 gün ile 1 hafta arasında tamamlanır."),
            ("Tanıtım filmi için ne tür içerikler sağlanmalı?", "Markanızın hikâyesi, hedef kitlesi, ürün veya hizmet detayları gibi bilgilerle birlikte varsa logo, kurumsal renkler ve önceki tanıtım materyalleri paylaşılmalıdır."),
            ("Tanıtım filmi hangi platformlarda kullanılabilir?", "Hazırlanan tanıtım filmi; web sitenizde, sosyal medya kanallarında, fuarlarda, sunumlarda ve reklam kampanyalarında rahatlıkla kullanılabilir."),
        ],
    },
    {
        "title": "E-Ticaret Sistemleri",
        "slug": "e-ticaret-sistemleri",
        "image": "services/e-ticaret-sistemleri.jpg",
        "tags": "E-Ticaret, Entegrasyon, Ödeme Sistemleri",
        "short": "Hedef kitlenizin kolayca kullanabileceği, sade, işlevsel ve satış odaklı e-ticaret siteleri tasarlıyoruz.",
        "intro": "Hedef kitlenizin kolayca kullanabileceği, sade ve işlevsel e-ticaret siteleri tasarlıyoruz. Müşterilerinizin ürünlere hızlıca göz atabileceği, kolay sipariş verebileceği ve rahat ödeme yapabileceği bir kullanıcı deneyimi sunuyoruz.",
        "overview": (
            "<p><strong>SEO uyumlu e-ticaret siteleri:</strong> Anahtar kelime kullanımı, meta açıklamalar ve hızlı sayfa yüklenmesi gibi faktörlerle sitenizin arama motorlarında üst sıralarda yer almasını sağlıyoruz.</p>"
            "<p><strong>Güvenli ödeme sistemleri:</strong> iyzico, PayPal, Stripe gibi güvenilir ödeme altyapılarını entegre ediyor; kredi kartı, banka kartı ve kapıda ödeme gibi seçeneklerle satış sürecinizi çeşitlendiriyoruz.</p>"
            "<p><strong>Mobil uyumlu tasarım:</strong> Müşterilerinizin mobil cihazlardan rahatlıkla alışveriş yapabilmesi için %100 mobil uyumlu (responsive) tasarımlar sunuyoruz.</p>"
            "<p><strong>Ürün yönetim sistemleri:</strong> Kategori oluşturma, ürün ekleme ve fiyat güncelleme gibi işlemleri kolayca yapabileceğiniz kullanıcı dostu bir yönetim paneli tasarlıyoruz.</p>"
            "<p><strong>Çoklu dil ve para birimi:</strong> E-ticaret sitenizi global pazara açmak için çoklu dil ve para birimi seçenekleri ekliyoruz.</p>"
        ),
        "features": [
            ("SEO Uyumlu Altyapı", "Markanızın dijital görünürlüğünü artırır, potansiyel müşterilerinizin sizi daha kolay bulmasını sağlar."),
            ("Hızlı ve Güvenli", "Hızlı ve güvenli altyapı ile müşteri memnuniyetini en üst seviyeye çıkarır."),
            ("Kolay Yönetilebilir", "Sitenizi kolayca güncelleyebilir, içeriklerinizi hızlıca yönetebilirsiniz."),
            ("Mobil Uyumlu Tasarım", "Her ekranda kusursuz performans ve görünüm."),
        ],
        "offerings": [
            ("Kullanıcı Odaklı ve Satışa Dönük Altyapı", "Modern tasarım\nHızlı yükleme\nGüvenli alışveriş deneyimi\nYüksek dönüşüm odaklı arayüz"),
            ("Entegrasyon ve Otomasyon", "Ödeme sistemleri\nKargo firmaları\nMuhasebe yazılımları\nStok ve sipariş yönetimi\nFatura ve pazaryeri entegrasyonları"),
            ("Yayın Sonrası Destek", "Test ve optimizasyon\nPanel eğitimi\nTeknik destek\nAnaliz ve ölçeklendirme"),
        ],
        "steps": [
            ("Analiz & Strateji", "İş modeliniz, hedef kitleniz, rakipleriniz ve ürün yapınız değerlendirilerek doğru altyapı ve tasarım stratejisi belirlenir."),
            ("Tasarım & Arayüz", "Kullanıcı deneyimi odaklı, güven veren ve dönüşüm sağlayan arayüz tasarımı hazırlanır."),
            ("Kurulum & Entegrasyonlar", "Ödeme, kargo, stok, fatura ve güvenlik entegrasyonları uygulanarak sistem hazır hale getirilir."),
            ("Test, Yayın & Eğitim", "Performans ve güvenlik testlerinin ardından site yayına alınır, panel kullanım eğitimi verilir."),
        ],
        "faqs": [],
    },
    {
        "title": "Web Tasarım",
        "slug": "web-tasarim",
        "image": "services/web-tasarim.jpg",
        "tags": "Kurumsal Web, Frontend, Backend, SEO",
        "short": "Markanızı en iyi yansıtan, hızlı, mobil uyumlu ve kolay yönetilebilir web siteleri tasarlıyoruz.",
        "intro": "Web tasarımda sizi öne çıkaralım. Markanızı en iyi yansıtan, hızlı, mobil uyumlu, arama motoru dostu ve panelden kolayca yönetilebilen web siteleri tasarlıyor ve geliştiriyoruz.",
        "overview": (
            "<p>Web siteniz, markanızın dijital dünyadaki vitrinidir. Bitasarımlazım olarak kullanıcı odaklı arayüzler, güçlü yazılım altyapısı ve SEO kriterlerine uygun yapıyı bir araya getirerek markanızın dijitalde güçlü bir yer edinmesini sağlıyoruz.</p>"
            "<p>Her projeye işletmenizi, hedef kitlenizi ve rakiplerinizi anlamakla başlıyor; marka kimliğinize uygun özgün bir tasarım dili oluşturuyoruz. Sonuç: hızlı açılan, her cihazda kusursuz görünen ve ziyaretçiyi müşteriye dönüştüren web siteleri.</p>"
        ),
        "features": [
            ("Keşif & Araştırma", "İşletmenizi, kitlenizi ve rakiplerinizi anlamak."),
            ("Konsept Geliştirme", "İlk marka konseptlerini ve tasarım fikirlerini oluşturmak."),
            ("İyileştirme & Test", "Görselleri mükemmelleştirmek ve kitlenizle uyumunu doğrulamak."),
            ("Final Uygulama", "Detaylı stil kılavuzu ile tüm marka varlıklarını teslim etmek."),
        ],
        "offerings": [
            ("Kurumsal Web Siteleri", "Markaya özel arayüz tasarımı\nMobil uyumlu yapı\nKolay içerik yönetim paneli"),
            ("SEO ve Performans", "Teknik SEO altyapısı\nHızlı yükleme süreleri\nAnalytics ve Search Console kurulumu"),
            ("Bakım ve Destek", "Güvenlik güncellemeleri\nDüzenli yedekleme\nİçerik güncelleme desteği"),
        ],
        "steps": [
            ("Tasarım", "Sizin için en doğru konsepti ve arayüzü tasarlıyoruz."),
            ("Geliştirme", "Sitenizi hızlı, güvenli ve yönetilebilir bir altyapıyla kodluyoruz."),
            ("Görsel Hazırlık", "Web sitenize uygun görseller ve içerikler hazırlanır."),
            ("Teslim", "Testlerin ardından siteniz yayına alınır ve panel eğitimi verilir."),
        ],
        "faqs": [
            ("Web sitesi tasarımı ne kadar sürer?", "Web sitesi tasarım süresi projenin kapsamına ve taleplere göre değişir. Basit bir kurumsal site genellikle 2–6 gün içinde, kapsamlı projeler ise birkaç hafta içinde tamamlanır."),
        ],
    },
    {
        "title": "Mobil Uygulama (App)",
        "slug": "mobil-uygulama-app",
        "image": "services/mobil-uygulama.jpg",
        "tags": "iOS, Android, UI/UX, API",
        "short": "iOS ve Android'de kusursuz çalışan, kullanıcı dostu ve performans odaklı mobil uygulamalar geliştiriyoruz.",
        "intro": "İşletmelerin mobil dünyada fark yaratmasını sağlamak için yenilikçi ve kullanıcı dostu mobil uygulama ve yazılım çözümleri sunuyoruz. iOS ve Android platformlarında kusursuz çalışan, performans odaklı uygulamalar geliştiriyoruz.",
        "overview": (
            "<p><strong>Özel mobil uygulama geliştirme:</strong> İşletmenizin ihtiyaçlarına göre sıfırdan, esnek, ölçeklenebilir ve güvenli uygulamalar geliştiriyoruz.</p>"
            "<p><strong>Kurumsal yazılım geliştirme:</strong> İç süreçlerinizi kolaylaştıracak CRM, ERP ve e-ticaret platformları için entegre yazılım çözümleri sağlıyoruz.</p>"
            "<p><strong>UI/UX tasarımı:</strong> Kullanıcı deneyimini ön planda tutan sade ve işlevsel arayüzler tasarlıyoruz.</p>"
            "<p><strong>Uygulama optimizasyonu:</strong> Mevcut uygulamanızın hızını ve kullanıcı memnuniyetini artırmak için optimizasyon ve güncellemeler yapıyoruz.</p>"
            "<p><strong>E-ticaret mobil uygulamaları:</strong> Müşterilerinizin ürünlerinize her an kolayca ulaşmasını sağlayan özel uygulamalar geliştiriyoruz.</p>"
        ),
        "features": [
            ("Arayüz (UX/UI)", "Mobil ekranlara uygun, sade, hızlı, modern ve sezgisel arayüz tasarımı."),
            ("Çapraz Platform ve Native", "Android, iOS veya her iki platform için yüksek performanslı geliştirme."),
            ("Entegrasyon ve Güvenli Altyapı", "API, ödeme, harita, bildirim ve CRM entegrasyonları; veri güvenliği ön planda."),
            ("Test ve Yayınlama", "Testlerin ardından mağazalarda yayın, sonrasında bakım ve geliştirme desteği."),
        ],
        "offerings": [
            ("Tasarım & Deneyim", "Kullanıcı yolculuğu analizi ve UX/UI tasarım\nModern, sade ve mobil uyumlu arayüz\nMarka kimliğine göre görsel konsept\nPrototip ve ön izleme"),
            ("Güçlü ve Güvenli Yazılım", "Android & iOS için native veya cross-platform\nAPI, ödeme, harita, bildirim ve CRM entegrasyonları\nGüvenlik standartlarına uygun mimari\nÖlçeklenebilir ve performans odaklı kod"),
            ("Yayınlama ve Destek", "App Store ve Google Play yayın desteği\nTest, performans ölçümü ve hata analizi\nGüncelleme, bakım ve geliştirme\nUzun dönem çözüm ortaklığı"),
        ],
        "steps": [
            ("Analiz & Planlama", "İş hedefleri, kullanıcı ihtiyaçları ve proje kapsamı belirlenir; teknik ve tasarımsal yol haritası hazırlanır."),
            ("UX/UI Tasarım", "Kullanıcı akışları, ekran şemaları ve son arayüz tasarımları oluşturulur."),
            ("Yazılım Geliştirme", "Uygulama geliştirilir, gerekli API ve üçüncü parti entegrasyonlar uygulanır."),
            ("Test, Yayın & Destek", "Testlerin ardından uygulama mağazalara yüklenir; bakım ve geliştirme desteği sağlanır."),
        ],
        "faqs": [
            ("Proje geliştirme süresi ne kadar sürer?", "Uygulamanın kapsamına göre süre değişiklik gösterebilir. Ortalama bir proje 4–12 hafta arasında tamamlanabilir."),
            ("Hem Android hem de iOS için uygulama geliştirebiliyor musunuz?", "Evet, talebinize göre Android, iOS veya her iki platform için native veya cross-platform çözümler sunuyoruz."),
            ("Uygulama yayınlama işlemlerini siz mi yapıyorsunuz?", "Evet, App Store ve Google Play yayın süreçleri tarafımızca yönetilir, gerekli açıklamalar ve görseller hazırlanır."),
            ("Uygulama güvenliği için hangi önlemler alınıyor?", "Veri güvenliği, güvenli bağlantı, kullanıcı doğrulama ve gizlilik ilkeleri doğrultusunda gerekli güvenlik standartları uygulanır."),
            ("Proje tesliminden sonra destek sağlıyor musunuz?", "Evet, ihtiyaç halinde bakım, güncelleme, hata düzeltme ve ek özellik geliştirme desteği sunuyoruz."),
        ],
    },
    {
        "title": "Outdoor Reklam Tasarımları",
        "slug": "outdoor-reklam-tasarimlari",
        "image": "services/outdoor-reklam.jpg",
        "tags": "Billboard, Açık Hava, Araç Giydirme",
        "short": "Billboard, raket, totem, araç giydirme ve cephe kaplama gibi dış mekân reklamlarında dikkat çeken tasarımlar.",
        "intro": "Markaların dış mekânda geniş kitlelere etkili bir şekilde ulaşmasını sağlamak için profesyonel outdoor reklam tasarımı hizmeti sunuyoruz. Billboard, raket, totem, araç giydirme ve bina cephe kaplama gibi alanlarda markanızın görünürlüğünü artırıyoruz.",
        "overview": (
            "<p><strong>Dikkat çekici ve yaratıcı tasarımlar:</strong> Hedef kitlenizin ilgisini çekecek, mesajınızı net ve etkili şekilde iletecek dış mekân reklamları tasarlıyoruz.</p>"
            "<p><strong>Farklı formatlara uygun tasarımlar:</strong> Billboard, afiş, raket, araç giydirme, durak reklamları ve totem gibi birçok alana özgün çözümler sunuyoruz.</p>"
            "<p><strong>Kurumsal kimlikle uyum:</strong> Markanızın kimliğiyle tutarlı tasarımlarla kurumsal imajınızı güçlendiriyoruz.</p>"
            "<p><strong>Yüksek çözünürlük:</strong> Büyük boyutlu reklam alanları için tasarımlarınızın her koşulda net ve profesyonel görünmesini sağlıyoruz.</p>"
        ),
        "features": [
            ("Stratejik Konum", "Lokasyon, hedef kitle davranışı ve görünürlük şartlarına göre planlama."),
            ("Dikkat Çeken Tasarım Dili", "Kalabalık alanlarda hızlı algılanan, akılda kalıcı görsel etki."),
            ("Marka Kimliğine Uyum", "Kurumsal renkler, logo kullanımı ve iletişim dili ile tam uyum."),
            ("Baskı ve Uygulama", "Billboard, folyo, araç giydirme, totem ve ışıklı tabela için doğru ölçü ve çözünürlük."),
        ],
        "offerings": [],
        "steps": [
            ("İhtiyaç Analizi", "Markanın hedefi, kullanılacak alan, hedef kitle ve mesaj belirlenir."),
            ("Tasarım Geliştirme", "Hızlı algılanabilir, dikkat çekici ve markaya uygun konsept oluşturulur."),
            ("Onay & Revizyon", "Tasarım tarafınıza sunulur, gerekirse revizyonlar yapılır."),
            ("Uygulama Hazırlığı", "Baskı tekniklerine uygun çözünürlük ve formatta teslim sağlanır."),
        ],
        "faqs": [],
    },
    {
        "title": "Google Reklam Yönetimi",
        "slug": "google-reklam-yonetimi",
        "image": "services/google-reklam.jpg",
        "tags": "Google Ads, Performans, Remarketing",
        "short": "Google Ads ile hedef kitlenize doğru zamanda ulaşmanızı sağlıyor, bütçenizi verimli kullanarak maksimum dönüşüm elde ediyoruz.",
        "intro": "Dijital pazarlamada başarıya ulaşmanın en güçlü yollarından biri Google reklamlarıdır. İşletmenizin dijital varlığını büyütmek ve hedef kitlenize en etkili şekilde ulaşmanız için profesyonel Google reklam hesabı yönetimi sunuyoruz.",
        "overview": (
            "<h3>Kapsamlı Reklam Stratejisi</h3><p>Hedeflerinizi, sektörünüzü ve rekabeti analiz ederek size özel bir reklam stratejisi geliştiriyoruz.</p>"
            "<h3>Anahtar Kelime Araştırması</h3><p>Potansiyel müşterilerinizin en çok aradığı kelimeleri belirleyerek tıklama başı maliyetleri düşürüyor, geri dönüşü artırıyoruz.</p>"
            "<h3>Kampanya Yönetimi ve Optimizasyon</h3><p>Kampanyalarınızı yakından izliyor, düzenli analizlerle yatırım getirinizi (ROI) artırıyoruz.</p>"
            "<h3>A/B Testleri ve Raporlama</h3><p>Farklı varyasyonları test ediyor, her ay şeffaf raporlarla performansınızı paylaşıyoruz.</p>"
            "<h3>Remarketing (Yeniden Pazarlama)</h3><p>Sitenizi daha önce ziyaret eden kullanıcılara yönelik reklamlarla kaçan potansiyel müşterileri geri kazanıyoruz.</p>"
        ),
        "features": [
            ("Hedef Kitle Odaklı Reklamlar", "Doğru zamanda, doğru kişilere ulaşmanızı sağlayan hassas hedefleme."),
            ("Bütçe Dostu Kampanya", "Reklam harcamalarınızı verimli kullanarak maksimum geri dönüş."),
            ("Performans Takibi", "Kampanya sonuçlarını düzenli analiz edip stratejiyi optimize ederiz."),
            ("Reklam Metni ve Görsel Optimizasyonu", "Tıklama oranını artıran yaratıcı reklam içerikleri."),
        ],
        "offerings": [
            ("Kampanya Yönetimi", "Hedef kitle analizi\nReklam metni ve görsel tasarımı\nBütçe planlaması ve yönetimi"),
            ("Performans Takibi ve Raporlama", "Düzenli analiz\nDetaylı raporlama\nOptimizasyon"),
            ("Strateji ve Danışmanlık", "Pazar araştırması\nStratejik planlama\nSürekli destek"),
        ],
        "steps": [
            ("Hedef & Strateji", "İşletmenizin hedefleri ve bütçesi doğrultusunda en uygun reklam stratejisini belirliyoruz."),
            ("Kampanya Kurulumu", "Reklam metinleri, görseller ve hedefleme seçenekleriyle etkili kampanyalar oluşturuyoruz."),
            ("Yayınlama ve İzleme", "Kampanyaları aktif hale getirip performansını sürekli takip ediyoruz."),
            ("Analiz ve Optimizasyon", "Elde edilen verilerle kampanyaları optimize ederek maksimum verim sağlıyoruz."),
        ],
        "faqs": [
            ("Google Ads nedir ve işletmem için neden önemli?", "Google Ads, hedef kitlenize ulaşmanızı sağlayan dijital reklam platformudur. İşletmenizin görünürlüğünü artırır ve potansiyel müşterilerle buluşmanızı kolaylaştırır."),
            ("Kampanya bütçemi nasıl belirlemeliyim?", "Bütçe, işletmenizin hedeflerine ve sektör rekabetine göre şekillenir. Bütçenizin en verimli şekilde kullanılması için size özel planlama yapıyoruz."),
            ("Reklamlarım ne kadar sürede görünür?", "Kampanyanız yayına alındıktan sonra reklamlarınız hemen görünür. En iyi sonuçlar için düzenli optimizasyon gerekir."),
        ],
    },
]

GENERAL_FAQS = [
    ("Sosyal medyada içerik paylaşım sıklığı ne olmalı?", "İçerik paylaşım sıklığı hedef kitlenize bağlı olarak değişir. Ancak düzenli ve dengeli bir paylaşım takvimi oluşturmak genellikle en iyi sonucu verir."),
    ("Sosyal medya yönetimi için en iyi strateji nedir?", "Her işletme için en iyi strateji farklı olabilir; ancak genel olarak hedef kitlenize uygun içerikler oluşturmak, düzenli ve tutarlı paylaşımlar yapmak ve geri bildirimlere hızlı cevap vermek önemlidir."),
    ("Web sitesi tasarımı ne kadar sürer?", "Web sitesi tasarım süresi projenin karmaşıklığına ve müşteri taleplerine göre değişir. Genellikle basit bir site tasarımı 2–6 gün içinde tamamlanabilir."),
    ("Kurumsal tanıtım filmi çekimi ne kadar sürer?", "Çekim süresi markanın ihtiyaçlarına, mekân sayısına ve senaryoya göre değişir. Genellikle 1 günlük çekim yeterlidir; kurgu ve montajla birlikte toplam teslim süresi 2–7 gün arasındadır."),
    ("Tanıtım filminde senaryoyu kim hazırlıyor?", "Senaryo; markanın hedef kitlesi, hizmetleri ve kurumsal kimliği dikkate alınarak ekibimiz tarafından hazırlanır. İstenirse marka tarafından verilen bilgilerle birlikte geliştirilir ve onayın ardından çekime geçilir."),
]

BRANDS = [
    ("Aktaş Müzik Evi", "aktas-muzik"), ("Carbotox", "carbotox"), ("Asant Dere Bungalov", "derotel"),
    ("Erfelek Fındık Atölyesi", "erfelek"), ("Eva Metal", "eva-metal"), ("Foks Petshop", "foks"),
    ("Grand Gurme", "grandgurme"), ("İstikbal", "istikbal"), ("Mutlu Trans", "mutlu-trans"),
    ("Özge Orman", "ozge-orman"), ("Aktivite Akademisi", "ref-2"), ("Turkuvaz Koleji", "referans-logo-mock_kopya"),
    ("Şengül", "sengul"), ("T-Shirt Zone", "tshirtzone"), ("Yücelin Çiftliği", "yucelicitligi"),
]

TESTIMONIALS = [
    ("Elif Y.", "Butik Kurucusu", "testimonials/yorum-2.jpg",
     "Online satışa geçiş sürecimizde web sitemizin hem şık hem de kullanıcı dostu olması bizim için kritikti. Modern tasarım dilleri ve mobil odaklı yaklaşımları sayesinde tam hayalimizdeki e-ticaret altyapısına kavuştuk. Ekip teknik süreci başından sonuna kadar kusursuz yönetti."),
    ("Ahmet K.", "Kurum Müdürü", "testimonials/yorum-3.jpg",
     "Okulumuzun vizyonunu dijital dünyaya taşımak ve kayıt dönemlerindeki sosyal medya kampanyalarımızı daha profesyonel hale getirmek istiyorduk. Kurumsal kimlik çalışmaları ve hedef odaklı reklam stratejileriyle velilerimizden harika geri dönüşler alıyoruz. Gerçekten markamıza ne lazımsa onu sundular."),
    ("Dekoratif Mum Markası", "Kurumsal kimlik & satış stratejisi", "testimonials/yorum-1.jpg",
     "Dekoratif mum üretimi yapıyoruz. Kurumsal kimliğimiz konusunda destek aldık, ayrıca satış stratejileri konusunda da oldukça ilgi gösterdiler. Teşekkürler!"),
    ("Caner D.", "Proje Yöneticisi", "",
     "Sektördeki karmaşık operasyon süreçlerini son kullanıcıya en basit ve modern şekilde sunmak istiyorduk. Platformumuzun arayüz tasarımı ve kullanıcı deneyimi konusunda mükemmel bir iş çıkardılar."),
    ("İşletme Sahibi", "Sosyal medya yönetimi müşterisi", "",
     "Aldığımız sosyal medya yönetimi hizmetinde arayınca ulaşabildiğimiz ve isteklerimize hızla hareket eden güvenilir bir firma."),
]

PROJECTS = [
    {"title": "Model Çekimleri", "category": "Fotoğraf & Video", "cover": "portfolio/model-cekimi.jpg",
     "images": ["portfolio/model-cekimi-yatay.jpg"], "strip": "Model Çekimi", "color": "brand", "services": ["tanitim-filmi-cekimi"],
     "summary": "Moda ve ürün odaklı markalar için konsept belirleme, stüdyo kurulumu, çekim ve rötuş süreçlerini uçtan uca yönettiğimiz model çekimleri.",
     "tags": "Fotoğraf, Moda, Stüdyo"},
    {"title": "E-Ticaret & Katalog", "category": "E-Ticaret", "cover": "portfolio/e-ticaret.jpg",
     "images": ["portfolio/e-ticaret-yatay.jpg"], "strip": "E-Ticaret", "color": "light", "services": ["e-ticaret-sistemleri"],
     "summary": "Ürün kataloğundan ödeme adımına kadar dönüşüm odaklı tasarlanan, entegrasyonları tamamlanmış e-ticaret altyapısı.",
     "tags": "E-Ticaret, Katalog, Ödeme Sistemi"},
    {"title": "Sosyal Medya Yönetimi", "category": "Sosyal Medya", "cover": "portfolio/sosyal-medya.jpg",
     "images": ["portfolio/sosyal-medya-yatay.jpg"], "strip": "Sosyal Medya", "color": "gray", "services": ["sosyal-medya-yonetimi"],
     "summary": "Facebook, Instagram ve LinkedIn için içerik planı, kreatif tasarım, reels üretimi ve topluluk yönetimi.",
     "tags": "Facebook, Instagram, LinkedIn"},
    {"title": "Limlapp.com", "category": "Web & Mobil", "cover": "portfolio/limlapp.jpg", "client": "Limlapp", "year": "2023",
     "images": [], "strip": "Limlapp", "color": "brand", "services": ["web-tasarim", "mobil-uygulama-app"],
     "summary": "Web ve mobilde tutarlı bir deneyim sunan, SEO uyumlu ve mobil öncelikli dijital ürün.",
     "tags": "Web, Mobil, SEO Uyumlu"},
    {"title": "Erfelek Fındık Atölyesi", "category": "Kurumsal Kimlik", "cover": "brands/erfelek.jpg", "client": "Erfelek Fındık",
     "images": [], "strip": "Erfelek", "color": "dark", "services": [], "featured": False,
     "summary": "Yerel bir üreticinin hikâyesini taşıyan logo ve kurumsal kimlik çalışması.",
     "tags": "Logo, Kurumsal Kimlik"},
    {"title": "Taksi Şimdi", "category": "Web & Mobil", "cover": "services/mobil-uygulama.jpg",
     "images": [], "strip": "Taksi Şimdi", "color": "light", "services": ["mobil-uygulama-app"], "featured": False,
     "summary": "Kullanıcıların hızlıca taksi çağırabilmesi için tasarlanan mobil uygulama arayüzü ve altyapısı.",
     "tags": "Mobil Uygulama, UI/UX"},
]

GALLERY = [
    ("Ofis", [("misc/ofis.jpg", "Ofisimiz"), ("misc/calisma-alani.jpg", "Çalışma alanı"), ("misc/karakter.jpg", "Bitasarımlazım karakteri")]),
    ("Çekimler", [("misc/kreatif-ekipman.jpg", "Prodüksiyon ekipmanları"), ("services/tanitim-filmi-cekimi.jpg", "Tanıtım filmi çekimi"),
                  ("portfolio/model-cekimi.jpg", "Model çekimi"), ("portfolio/model-cekimi-yatay.jpg", "Stüdyo çekimi")]),
    ("Projeler", [("portfolio/e-ticaret-yatay.jpg", "E-ticaret kampanyası"), ("portfolio/sosyal-medya-yatay.jpg", "Sosyal medya içerikleri"),
                  ("misc/yapay-zeka.jpg", "Üretken yapay zekâ"), ("services/outdoor-reklam.jpg", "Outdoor reklam"), ("misc/renkler.jpg", "Renk çalışması")]),
]

STATS = [("12+", "Yıllık deneyim", "2013'ten bu yana"), ("600+", "Mutlu müşteri", "Bize güvenen markalar"),
         ("2", "Şehir ofisi", "Bolu & İstanbul"), ("4,8/5", "Müşteri puanı", "85 değerlendirmeye göre")]


def S(type, **kw):
    """Bölüm tanımı kısayolu."""
    kw["type"] = type
    return kw


PAGES = [
    {
        "key": "home", "slug": "anasayfa", "title": "Ana Sayfa",
        "meta_title": "Bitasarımlazım - Bolu Sosyal Medya Ajansı | Web Tasarım & Dijital Pazarlama",
        "sections": [
            S("hero_home", title="İyi işler şansa bırakılmaz,\n{bize bırakılır}",
              subtitle="Sosyal Medya Yönetimi\nTanıtım Filmi\nE-Ticaret\nWeb Tasarım\nMobil Uygulama\nOutdoor Reklam\nGoogle Ads",
              button_text="Gel, Tanışalım", button_url="/iletisim/",
              items=[{"image": "portfolio/model-cekimi.jpg", "title": "Model Çekimleri"},
                     {"image": "services/tanitim-filmi-cekimi.jpg", "title": "Tanıtım Filmi"},
                     {"image": "misc/yapay-zeka.jpg", "title": "Üretken Yapay Zekâ"},
                     {"image": "portfolio/e-ticaret.jpg", "title": "E-Ticaret"}]),
            S("statement", eyebrow="Bitasarımlazım Medya Ajansı",
              title="2013'ten beri ülke çapında yüzlerce projeye [çözüm] ürettik.",
              body="<p>Stratejiden dağıtıma kadar en son teknolojiyi yaratıcılıkla birleştiriyoruz. Öğrenen, uyum sağlayan ve gelişen dijital ürünler üreterek müşterilerimizin daha hızlı yenilik yapmasına, daha akıllı çalışmasına ve kullanıcılarına daha iyi deneyimler sunmasına yardımcı oluyoruz.</p>",
              button_text="Tanışalım mı?", button_url="/hakkimizda/"),
            S("logo_marquee", name="Referans bandı"),
            S("featured_work", eyebrow="Portföyümüz", title="Geleceği {yeniden} tasarlıyoruz",
              button_text="Tüm işler", button_url="/portfoy/", limit=4),
            S("big_headline", title="Her markayı\n[güvenle] büyütürüz",
              subtitle="Vizyon için her markaya bi tasarım lazım",
              body="<p>Her markanın ihtiyaçlarına özel geliştirdiğimiz çözümlerle dijital deneyimi daha işlevsel, erişilebilir ve etkili hale getiriyoruz. Teknolojinin imkânlarını yaratıcı dokunuşlarla buluşturup işletmelerin dijitalde güçlü ve sürdürülebilir bir varlık oluşturmasını sağlıyoruz.</p>",
              button_text="Bi Merhaba De", button_url="/iletisim/"),
            S("capabilities", eyebrow="Neler Yapıyoruz",
              subtitle="Markanızın dijital dünyada neye ihtiyacı varsa; etkili bir varlık, güçlü bir bağ ve sürdürülebilir büyüme için size tam olarak bi tasarım lazım.",
              button_text="Tüm Hizmetler", button_url="/hizmetler/"),
            S("stats", eyebrow="Rakamlarla Biz", title="İyi işler [şansa] bırakılmaz", items=[{"value": v, "title": t, "text": x} for v, t, x in STATS]),
            S("testimonials", eyebrow="Referanslarımız", title="Müşterilerimiz {ne diyor?}", subtitle="4,8/5 — 85 değerlendirmeye göre"),
            S("faq", eyebrow="En Çok Aldığımız Sorular", title="Sorularınıza hızlı yanıt",
              subtitle="Aklınıza takılan başka bir soru varsa bize yazmanız yeterli.", button_text="Bize Sorun", button_url="/iletisim/"),
            S("blog_latest", eyebrow="Dijital Rehber", title="Tasarım, teknoloji ve {dijital pazarlama}",
              button_text="Tümünü Oku", button_url="/blog/", limit=3),
            S("cta", title="Fikirlerinizi [gerçeğe] dönüştürün", subtitle="Kahve eşliğinde projenizi konuşalım.",
              button_text="Hadi Başlayalım", button_url="/iletisim/"),
            S("image_band", image="misc/calisma-alani.jpg"),
        ],
    },
    {
        "key": "about", "slug": "hakkimizda", "title": "Hakkımızda",
        "meta_description": "Bitasarımlazım; 2013'ten bu yana Bolu ve İstanbul ofislerinden markalara strateji, tasarım ve teknolojiyi bir araya getiren dijital çözümler sunar.",
        "sections": [
            S("page_hero", eyebrow="Hakkımızda", title="Her markaya\n{bi tasarım} lazım",
              subtitle="Vizyoner tasarımcılardan oluşan ekibimiz büyüleyici markalar oluşturur. 2013'ten bu yana stratejiyi, yaratıcılığı ve teknolojiyi bir araya getiriyoruz.",
              image="misc/karakter.jpg"),
            S("stats", items=[{"value": v, "title": t, "text": x} for v, t, x in STATS]),
            S("text_media", eyebrow="Dijital dönüşümde teknoloji ve tasarımın gücü", title="Sadece estetik değil,\n[veriye dayalı]",
              subtitle="Markanızı geleceğe taşıyoruz",
              body="<p>Sadece estetik değil, veriye dayalı stratejiler ve en yeni teknolojilerle markanızı geleceğe taşıyoruz. Logo tasarımından video tanıtıma kadar hedef kitlenize doğru mesajı, doğru mecrada ulaştırıyoruz.</p>",
              image="misc/ofis.jpg", button_text="Hizmetlerimiz", button_url="/hizmetler/",
              items=[{"title": t} for t in ["Veriye Dayalı Planlamalar", "Modern ve Minimalist Kurumsal Kimlik", "Üretken Yapay Zekâ (AI)",
                                             "'Mobile-First' Yaklaşımlı Güçlü Yazılım", "İleri Seviye Video Kurgu",
                                             "Uçtan Uca E-Ticaret ve Dijital Ekosistem", "Veri Odaklı Performans"]]),
            S("faq", theme="gray", eyebrow="Bitasarımlazım Hakkında", title="Merak {edilenler}",
              items=[
                  {"title": "Hangi hizmetleri sunuyorsunuz?", "text": "Logo ve kurumsal kimlik tasarımı, web sitesi ve e-ticaret çözümleri, sosyal medya yönetimi, içerik üretimi ve Meta reklamları başta olmak üzere uçtan uca dijital pazarlama hizmetleri sunuyoruz."},
                  {"title": "Proje süreci nasıl ilerliyor?", "text": "Her proje ihtiyaç analizi ve hedef belirleme aşamasıyla başlar. Ardından strateji, tasarım ve uygulama süreçleri planlı şekilde yürütülür ve düzenli geri bildirimlerle proje tamamlanır."},
                  {"title": "Sizi diğer ajanslardan ayıran nedir?", "text": "Yaratıcı tasarımı veri odaklı stratejiyle birleştirmemiz, her projeye özel çözümler üretmemiz ve ölçülebilir sonuçlara odaklanmamız bizi farklı kılan en önemli unsurlardır."},
              ]),
            S("features", eyebrow="Neden Biz?", title="İyi işler şansa\n[bırakılmaz]",
              subtitle="Deneyimli strateji ekibimiz, hedeflerinize özel, ölçülebilir ve sonuç odaklı yol haritaları oluşturarak markanız için kalıcı değer yaratıyor.",
              items=[
                  {"title": "Uçtan Uca Dijital Çözümler", "text": "Logo tasarımından video tanıtıma, web sitesinden reklam yönetimine kadar markanızın tüm dijital ihtiyaçlarını tek çatı altında topluyoruz."},
                  {"title": "Sonuç Odaklı Stratejik Planlama", "text": "Hedef kitlenize doğru mesajı, doğru mecrada ulaştırıyor; her adımı ölçülebilir hedeflerle planlıyoruz."},
                  {"title": "Kesintisiz Teknik Destek", "text": "Yayın sonrasında da yanınızdayız; sürekli analiz ve iyileştirme ile büyümenizi sürdürülebilir kılıyoruz."},
              ]),
            S("marquee_text", subtitle="Analiz\nTasarım\nYazılım\nİçerik\nYönetim"),
            S("logo_marquee", title="Bize güvenen markalar"),
            S("cta", title="Herkese bi tasarım lazım,\nsen de [katıl]", subtitle="Ücretsiz danışmanlık için bir görüşme planlayın.",
              button_text="Görüşme Planla", button_url="/iletisim/", image="misc/calisma-alani.jpg"),
        ],
    },
    {
        "key": "services", "slug": "hizmetler", "title": "Hizmetler",
        "meta_description": "Sosyal medya yönetimi, tanıtım filmi, e-ticaret, web tasarım, mobil uygulama, outdoor reklam ve Google reklam yönetimi hizmetlerimiz.",
        "sections": [
            S("page_hero", eyebrow="Ne Yaparız", title="Eğlenerek\n{marka} yaratın",
              subtitle="İlgi çekici dijital deneyimler üretiyor, markalaşmadan geliştirmeye kadar ihtiyaçlarınıza uygun çözümleri uçtan uca sağlıyoruz."),
            S("services_list", subtitle="Stratejik tasarım yaklaşımıyla markaların sezgisel ve kullanıcı dostu dijital ürünler oluşturmasına yardımcı oluyoruz."),
            S("process", theme="gray", eyebrow="Fikirden koda, markanızı büyüten vizyon", title="Dijital dünyada size\nne [lazım?]",
              items=[{"title": "Araştırma & Analiz", "text": "Müşteri ihtiyaçlarını ve pazarı derinlemesine araştırıyoruz."},
                     {"title": "Tasarım & Prototip", "text": "Fikirleri somut çözümlere ve prototiplere dönüştürüyoruz."},
                     {"title": "Test & Yineleme", "text": "Geri bildirimlere göre iyileştirip mükemmelleştiriyoruz."},
                     {"title": "Hazırlık & Teslimat", "text": "Pürüzsüz bir lansmanla projenizi yayına alıyoruz."}]),
            S("marquee_text", subtitle="Analiz\nTasarım\nYazılım\nİçerik\nYönetim"),
            S("testimonials", eyebrow="Görüşler", title="Onlar {anlatsın}"),
            S("cta", title="Kahve eşliğinde projenizi [konuşalım]", button_text="Hadi Konuşalım", button_url="/iletisim/",
              button2_text="Projelerimize göz atın", button2_url="/portfoy/"),
        ],
    },
    {
        "key": "portfolio", "slug": "portfoy", "title": "Portföy",
        "meta_description": "Bitasarımlazım portföyü: sosyal medya, e-ticaret, web, mobil uygulama ve prodüksiyon projelerimiz.",
        "sections": [
            S("page_hero", eyebrow="Portföy Vitrini", title="Sınıfının en iyisi,\n{yerel} dokunuş",
              subtitle="Her markanın ihtiyaçlarına özel geliştirdiğimiz çözümlerle dijital deneyimi daha işlevsel, erişilebilir ve etkili hale getiriyoruz."),
            S("portfolio_grid"),
            S("cta", title="Sıradaki proje\n[sizinki] olsun", button_text="Bi Merhaba De", button_url="/iletisim/"),
        ],
    },
    {
        "key": "gallery", "slug": "galeri", "title": "Foto Galeri",
        "sections": [
            S("page_hero", eyebrow="Foto Galeri", title="Tasarım {alanı}",
              subtitle="Çekimlerimizden, ofisimizden ve projelerimizden kareler."),
            S("gallery_grid"),
        ],
    },
    {
        "key": "references", "slug": "referanslar", "title": "Referanslar",
        "meta_description": "Bitasarımlazım'a güvenen markalar ve müşteri yorumları.",
        "sections": [
            S("page_hero", eyebrow="Referanslarımız", title="600+ marka\n[bize güvendi]",
              subtitle="Bolu'dan İstanbul'a, farklı sektörlerden yüzlerce markanın dijital yolculuğunda yer aldık."),
            S("brands_grid"),
            S("testimonials", eyebrow="Görüşler", title="Müşterilerimiz {ne diyor?}", subtitle="4,8/5 — 85 değerlendirmeye göre"),
            S("cta", title="Referanslarımız arasına [katılın]", button_text="Bi Merhaba De", button_url="/iletisim/"),
        ],
    },
    {
        "key": "blog", "slug": "blog", "title": "Blog",
        "meta_description": "Strateji, tasarım, teknoloji ve dijital pazarlama üzerine yazılar.",
        "sections": [
            S("page_hero", eyebrow="İçgörü Günlüğü", title="Strateji, tasarım ve\nteknolojiyi {konuşuyoruz}",
              subtitle="Operasyonlarımızdan öğrendiklerimizi, trend analizlerini ve pratik ipuçlarını burada paylaşıyoruz."),
            S("blog_list", limit=9),
        ],
    },
    {
        "key": "contact", "slug": "iletisim", "title": "İletişim",
        "meta_description": "Bitasarımlazım ile iletişime geçin: Bolu ve İstanbul ofislerimiz, telefon, e-posta ve iletişim formu.",
        "sections": [
            S("contact_form", anchor="iletisim-formu", eyebrow="İletişime Geçin", title="Aklınızda bir\n[proje] mi var?",
              subtitle="Marka kimliği, web tasarımı veya dijital pazarlama konularında yardıma mı ihtiyacınız var? Fikirlerinizi nasıl hayata geçirebileceğimizi konuşalım."),
            S("faq", eyebrow="Sıkça Sorulan Sorular", title="Sorularınıza hızlı yanıt"),
        ],
    },
]


class Command(BaseCommand):
    help = "Eski siteden derlenen içeriklerle örnek verileri yükler."

    def add_arguments(self, parser):
        parser.add_argument("--reset", action="store_true", help="Mevcut içerikleri silip yeniden yükler.")

    def handle(self, *args, reset=False, **options):
        if Page.objects.exists() and not reset:
            self.stdout.write(self.style.WARNING("İçerik zaten var. Baştan yüklemek için --reset kullanın."))
            return
        with transaction.atomic():
            if reset:
                self._wipe()
            self._settings()
            self._navigation()
            services = self._services()
            self._faqs()
            self._brands()
            self._testimonials()
            self._projects(services)
            self._gallery()
            self._blog()
            self._pages()
        self.stdout.write(self.style.SUCCESS("Örnek içerikler yüklendi."))

    # ------------------------------------------------------------------ yardımcılar
    def _wipe(self):
        for model in (SectionItem, Section, Page, NavItem, SocialLink, Office, TextSnippet, ServiceFeature,
                      ServiceOffering, ServiceStep, FAQ, ProjectImage, Project, ProjectCategory, Service,
                      GalleryImage, GalleryCategory, Brand, Testimonial, Post, Category):
            model.objects.all().delete()
        SiteSettings.objects.all().delete()

    def _settings(self):
        s = SiteSettings.load()
        s.site_name = "Bitasarımlazım"
        s.tagline = "Bolu Sosyal Medya Ajansı"
        s.logo = media("site/logo-yellow.png")
        s.logo_footer = media("site/logo-yellow.png")
        s.logo_dark = media("site/logo-black.png")
        s.logo_mark = media("site/mark-yellow.png")
        s.favicon = media("site/favicon-512.png")
        s.og_image = media("site/og-default.jpg")
        s.email = "iletisim@bitasarimlazim.com"
        s.email_secondary = "info@bitasarimlazim.com"
        s.phone = "+90 546 244 44 14"
        s.whatsapp = "905462444414"
        s.footer_tagline = "İyi işler şansa bırakılmaz."
        s.footer_about = ("2013'ten beri Bolu ve İstanbul ofislerimizden ülke çapında markalara sosyal medya, web, "
                          "e-ticaret, reklam ve prodüksiyon çözümleri üretiyoruz.")
        s.meta_title = "Bitasarımlazım - Bolu Sosyal Medya Ajansı | Web Tasarım & Dijital Pazarlama"
        s.meta_description = ("Bolu ve İstanbul merkezli sosyal medya ajansı Bitasarımlazım; sosyal medya yönetimi, tanıtım "
                              "filmi, web tasarım, e-ticaret, mobil uygulama ve Google reklam yönetimi hizmetleri sunar.")
        s.meta_keywords = "bolu sosyal medya ajansı, bolu web tasarım, tanıtım filmi, e-ticaret, google ads, dijital pazarlama"
        s.notify_email = "iletisim@bitasarimlazim.com"
        s.save()

    def _navigation(self):
        header = [("Hakkımızda", "/hakkimizda/"), ("Hizmetler", "/hizmetler/"), ("Portföy", "/portfoy/"),
                  ("Galeri", "/galeri/"), ("Referanslar", "/referanslar/"), ("Blog", "/blog/"), ("İletişim", "/iletisim/")]
        footer = [("Ana Sayfa", "/"), ("Hakkımızda", "/hakkimizda/"), ("Hizmetler", "/hizmetler/"), ("Portföy", "/portfoy/"),
                  ("Referanslar", "/referanslar/"), ("Blog", "/blog/"), ("İletişim", "/iletisim/")]
        for i, (label, url) in enumerate(header):
            NavItem.objects.create(location="header", label=label, url=url, order=i)
        for i, (label, url) in enumerate(footer):
            NavItem.objects.create(location="footer", label=label, url=url, order=i)
        SocialLink.objects.create(platform="instagram", url="https://www.instagram.com/bitasarimlazim/", order=0)
        SocialLink.objects.create(platform="youtube", url="https://www.youtube.com/@bitasarimlazim", order=1)
        Office.objects.create(name="Bolu", order=0, dot_color="#F6C500",
                              address="Tabaklar Mah. Hattat Emin Barın Cd.\nÜnal İş Merkezi Kat:1 Daire:5\nMerkez / BOLU")
        Office.objects.create(name="İstanbul", order=1, dot_color="#F7F5F0",
                              address="Esentepe, 4. Levent Kavşağı No: 209\nŞişli / İSTANBUL")

    def _services(self):
        result = {}
        for i, d in enumerate(SERVICES):
            s = Service(title=d["title"], slug=d["slug"], short_description=d["short"], tags=d["tags"], intro=d["intro"],
                        overview=d["overview"], order=i, meta_description=d["short"])
            s.thumbnail = media(d["image"])
            s.cover = media(d["image"])
            s.save()
            for j, (t, x) in enumerate(d["features"]):
                ServiceFeature.objects.create(service=s, title=t, text=x, order=j)
            for j, (t, x) in enumerate(d["offerings"]):
                ServiceOffering.objects.create(service=s, title=t, items=x, order=j)
            for j, (t, x) in enumerate(d["steps"]):
                ServiceStep.objects.create(service=s, title=t, text=x, order=j)
            for j, (q, a) in enumerate(d["faqs"]):
                FAQ.objects.create(service=s, question=q, answer=a, order=j)
            result[s.slug] = s
        return result

    def _faqs(self):
        for i, (q, a) in enumerate(GENERAL_FAQS):
            FAQ.objects.create(question=q, answer=a, order=i)

    def _brands(self):
        for i, (name, file) in enumerate(BRANDS):
            b = Brand(name=name, order=i)
            b.logo = media(f"brands/{file}.jpg")
            b.save()

    def _testimonials(self):
        for i, (name, role, avatar, quote) in enumerate(TESTIMONIALS):
            t = Testimonial(name=name, role=role, quote=quote, order=i, rating=5)
            if avatar:
                t.avatar = media(avatar)
            t.save()

    def _projects(self, services):
        cats = {}
        for i, d in enumerate(PROJECTS):
            cat = cats.get(d["category"])
            if cat is None:
                cat = cats[d["category"]] = ProjectCategory.objects.create(name=d["category"], order=len(cats))
            p = Project(title=d["title"], category=cat, client=d.get("client", ""), year=d.get("year", ""),
                        strip_text=d["strip"], strip_color=d["color"], summary=d["summary"], tags=d["tags"],
                        is_featured=d.get("featured", True), order=i,
                        body=f"<p>{d['summary']}</p><p>Bu proje kapsamında markanın hedeflerine uygun strateji, tasarım ve uygulama süreçlerini birlikte yürüttük.</p>")
            p.cover = media(d["cover"])
            p.save()
            p.services.set([services[s] for s in d["services"] if s in services])
            for j, img in enumerate(d["images"]):
                pi = ProjectImage(project=p, order=j)
                pi.image = media(img)
                pi.save()

    def _gallery(self):
        order = 0
        for ci, (cat_name, images) in enumerate(GALLERY):
            cat = GalleryCategory.objects.create(name=cat_name, order=ci)
            for path, title in images:
                g = GalleryImage(category=cat, title=title, order=order)
                g.image = media(path)
                g.save()
                order += 1

    def _blog(self):
        posts = json.loads((SEED_DIR / "blog_posts.json").read_text(encoding="utf-8"))
        cats = {}
        now = timezone.now()
        for d in posts:
            cat = cats.get(d["category"])
            if cat is None:
                cat = cats[d["category"]] = Category.objects.create(name=d["category"], order=len(cats))
            p = Post(title=d["title"], slug=d["slug"], category=cat, excerpt=d["excerpt"], body=d["body"], tags=d["tags"],
                     author_name="Bitasarımlazım", status=Post.PUBLISHED, published_at=now - timedelta(days=d["order"] * 6))
            p.cover = media(d["cover"])
            p.save()

    def _pages(self):
        for pdata in PAGES:
            page = Page.objects.create(title=pdata["title"], slug=pdata["slug"], meta_title=pdata.get("meta_title", ""),
                                       meta_description=pdata.get("meta_description", ""))
            Page.objects.filter(pk=page.pk).update(system_key=pdata["key"])
            for order, sdata in enumerate(pdata["sections"]):
                sdata = dict(sdata)
                items = sdata.pop("items", [])
                image = sdata.pop("image", None)
                section = Section(page=page, order=order, **sdata)
                if image:
                    section.image = media(image)
                section.save()
                for j, item in enumerate(items):
                    item = dict(item)
                    img = item.pop("image", None)
                    si = SectionItem(section=section, order=j, **item)
                    if img:
                        si.image = media(img)
                    si.save()
        # Örnek özel sayfa (taslak): KVKK
        kvkk = Page.objects.create(title="KVKK Aydınlatma Metni", slug="kvkk", is_published=False, show_in_sitemap=False)
        Section.objects.create(page=kvkk, type="page_hero", order=0, title="KVKK {aydınlatma metni}", eyebrow="Yasal")
        Section.objects.create(
            page=kvkk, type="rich_text", order=1,
            body="<p>Bu sayfa panelden oluşturulmuş örnek bir taslaktır. Kişisel verilerin korunmasına ilişkin metninizi "
                 "hukuk danışmanınızla birlikte hazırlayıp buraya ekleyin ve sayfayı yayına alın.</p>",
        )
