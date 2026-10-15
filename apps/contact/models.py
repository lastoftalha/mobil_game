from django.db import models


class ContactMessage(models.Model):
    name = models.CharField("Ad soyad", max_length=150)
    email = models.EmailField("E-posta")
    phone = models.CharField("Telefon", max_length=40, blank=True)
    company = models.CharField("Şirket", max_length=150, blank=True)
    service = models.CharField("İlgilendiği hizmet", max_length=200, blank=True)
    message = models.TextField("Mesaj")
    consent = models.BooleanField("İletişim izni", default=False)
    page_url = models.CharField("Gönderildiği sayfa", max_length=300, blank=True)
    ip_address = models.GenericIPAddressField("IP", null=True, blank=True)
    is_read = models.BooleanField("Okundu", default=False)
    note = models.TextField("İç not", blank=True, help_text="Sadece panelde görünür.")
    created_at = models.DateTimeField("Tarih", auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]
        verbose_name = "Mesaj"
        verbose_name_plural = "Mesajlar"

    def __str__(self):
        return f"{self.name} — {self.created_at:%d.%m.%Y}"


class Subscriber(models.Model):
    email = models.EmailField("E-posta", unique=True)
    is_active = models.BooleanField("Aktif", default=True)
    created_at = models.DateTimeField("Kayıt tarihi", auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]
        verbose_name = "Bülten abonesi"
        verbose_name_plural = "Bülten aboneleri"

    def __str__(self):
        return self.email
