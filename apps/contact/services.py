import logging

from django.core.cache import cache
from django.core.mail import send_mail

logger = logging.getLogger(__name__)

RATE_LIMIT = 5          # pencere başına izin verilen gönderim
RATE_WINDOW = 10 * 60   # saniye


def client_ip(request):
    forwarded = request.META.get("HTTP_X_FORWARDED_FOR", "")
    if forwarded:
        return forwarded.split(",")[0].strip()
    return request.META.get("REMOTE_ADDR")


def rate_limited(request, scope="contact"):
    key = f"rl:{scope}:{client_ip(request)}"
    count = cache.get(key, 0)
    if count >= RATE_LIMIT:
        return True
    cache.set(key, count + 1, RATE_WINDOW)
    return False


def notify_new_message(site_settings, message):
    recipient = site_settings.notify_email or site_settings.email
    if not recipient:
        return
    body = (
        f"Ad Soyad: {message.name}\n"
        f"E-posta: {message.email}\n"
        f"Telefon: {message.phone}\n"
        f"Şirket: {message.company}\n"
        f"Hizmet: {message.service}\n\n"
        f"{message.message}\n"
    )
    try:
        send_mail(f"[{site_settings.site_name}] Yeni iletişim mesajı: {message.name}", body, None, [recipient])
    except Exception:  # e-posta hatası formu bozmasın
        logger.exception("İletişim bildirimi gönderilemedi")
