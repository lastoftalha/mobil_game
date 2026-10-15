"""Şablonlarda kullanılan sabit metinlerin varsayılanları.

Şablonda: {% t "anahtar" %}  — panelden "Sabit Metinler" ekranında düzenlenir.
Grup adı, anahtarın ilk noktaya kadar olan kısmından gelir.
"""

GROUPS = {
    "genel": "Genel",
    "menu": "Menü ve alt bilgi",
    "hizmet": "Hizmet detay sayfası",
    "proje": "Portföy",
    "blog": "Blog",
    "form": "İletişim formu",
    "galeri": "Galeri",
    "hata": "Hata sayfaları",
}

DEFAULTS = {
    # Genel
    "genel.devamini_oku": "Devamını Oku",
    "genel.icerige_gec": "İçeriğe geç",
    "genel.detaylar": "Detayları Gör",
    "genel.tumu": "Tümü",
    "genel.anasayfa": "Ana Sayfa",
    "genel.geri_don": "Geri Dön",
    "genel.kesfet": "Keşfet",
    "genel.oynat": "OYNAT",
    "genel.durdur": "DURDUR",
    "genel.cerez_kabul": "Kabul Et",
    "genel.cerez_detay": "Detaylı bilgi",
    "genel.whatsapp": "WhatsApp'tan yazın",
    "genel.yukari": "Yukarı",
    "genel.puan": "Müşteri puanı",
    # Menü / alt bilgi
    "menu.ac": "Menü",
    "menu.kapat": "Kapat",
    "menu.mobil_iletisim": "Bize ulaşın",
    "footer.site_haritasi": "Site Haritası",
    "footer.ofisler": "Ofisler",
    "footer.hizmetler": "Hizmetler",
    "footer.sosyal": "Sosyal",
    "footer.iletisim": "İletişim",
    "footer.bulten_baslik": "Bültenimize Katılın",
    "footer.bulten_placeholder": "E-posta adresiniz",
    "footer.bulten_buton": "Gönder",
    "footer.bulten_basarili": "Bültenimize kaydoldunuz. Teşekkürler!",
    "footer.bulten_hata": "Lütfen geçerli bir e-posta adresi girin.",
    # Hizmet detay
    "hizmet.etiket": "Hizmet",
    "hizmet.genel_bakis": "Hizmete Genel Bakış",
    "hizmet.ozellikler": "Özellikler",
    "hizmet.ne_sunuyoruz": "Ne Sunuyoruz?",
    "hizmet.surec_ust": "Çalışma Süreci",
    "hizmet.surec": "Çalışma Sürecimiz",
    "hizmet.sss": "Sıkça Sorulan Sorular",
    "hizmet.ilgili_isler": "İlgili İşler",
    "hizmet.diger": "Diğer Hizmetlerimiz",
    "hizmet.cta_baslik": "Uzmanlarla [işbirliği] yapmaktan çekinmeyin.",
    "hizmet.cta_buton": "Hadi Konuşalım",
    # Proje
    "proje.portfoy": "Portföy",
    "proje.musteri": "Müşteri",
    "proje.yil": "Yıl",
    "proje.kategori": "Kategori",
    "proje.hizmetler": "Hizmetler",
    "proje.siteyi_ziyaret": "Siteyi Ziyaret Et",
    "proje.sonraki": "Sonraki Proje",
    "proje.bos": "Henüz proje eklenmedi.",
    "proje.incele": "İncele",
    # Blog
    "blog.ara": "Başlık veya anahtar kelime arayın",
    "blog.ara_buton": "Ara",
    "blog.dk": "dk okuma",
    "blog.yazar": "Yazar",
    "blog.tarih": "Tarih",
    "blog.goruntulenme": "Görüntülenme",
    "blog.etiketler": "Etiketler",
    "blog.paylas": "Paylaş",
    "blog.ilgili": "İlgili Yazılar",
    "blog.bos": "Aradığınız kriterlere uygun yazı bulunamadı.",
    "blog.onceki": "Önceki",
    "blog.sonraki": "Sonraki",
    "blog.sonuc": "için sonuçlar",
    # Form
    "form.ad": "Ad Soyad",
    "form.eposta": "E-posta Adresi",
    "form.telefon": "Telefon (isteğe bağlı)",
    "form.sirket": "Şirket",
    "form.hizmet": "İlgilendiğiniz hizmet",
    "form.hizmet_sec": "Hizmet seçin",
    "form.mesaj": "Projenizden bahsedin",
    "form.izin": "Talebim ve ilgili hizmetler hakkında benimle iletişime geçilmesini kabul ediyorum.",
    "form.gonder": "Talep Gönder",
    "form.hata": "Lütfen işaretli alanları kontrol edin.",
    "form.cok_hizli": "Çok sık mesaj gönderdiniz. Lütfen biraz sonra tekrar deneyin.",
    "form.eposta_baslik": "E-posta",
    "form.telefon_baslik": "Telefon",
    "form.whatsapp_baslik": "WhatsApp",
    "form.harita": "Harita",
    # Galeri
    "galeri.bos": "Galeriye henüz görsel eklenmedi.",
    # Hata
    "hata.404_baslik": "Sayfa [bulunamadı]",
    "hata.404_metin": "Aradığınız sayfa taşınmış ya da hiç var olmamış olabilir.",
    "hata.500_baslik": "Bir şeyler [ters gitti]",
    "hata.500_metin": "Kısa süre içinde düzelteceğiz. Lütfen daha sonra tekrar deneyin.",
}


def group_of(key):
    prefix = key.split(".", 1)[0]
    if prefix == "footer":
        prefix = "menu"
    return GROUPS.get(prefix, prefix.title())
