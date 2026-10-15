from django.contrib import messages
from django.shortcuts import redirect
from django.utils.http import url_has_allowed_host_and_scheme
from django.views.decorators.http import require_POST

from apps.core.models import TextSnippet
from apps.core.snippets import DEFAULTS

from .forms import SubscribeForm
from .models import Subscriber
from .services import rate_limited


def _snippet(key):
    obj = TextSnippet.objects.filter(key=key).first()
    return obj.value if obj else DEFAULTS.get(key, key)


def _back(request):
    target = request.POST.get("next") or request.META.get("HTTP_REFERER") or "/"
    if not url_has_allowed_host_and_scheme(target, allowed_hosts={request.get_host()},
                                           require_https=request.is_secure()):
        target = "/"
    return target


@require_POST
def subscribe(request):
    form = SubscribeForm(request.POST)
    target = _back(request)
    if rate_limited(request, "newsletter"):
        messages.error(request, _snippet("form.cok_hizli"))
        return redirect(target)
    if form.is_valid():
        email = form.cleaned_data["email"].lower()
        Subscriber.objects.update_or_create(email=email, defaults={"is_active": True})
        messages.success(request, _snippet("footer.bulten_basarili"))
    else:
        messages.error(request, _snippet("footer.bulten_hata"))
    return redirect(f"{target.split('#')[0]}#footer")
