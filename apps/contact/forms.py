from django import forms

from .models import ContactMessage, Subscriber


class ContactForm(forms.ModelForm):
    # Bot tuzağı: gerçek kullanıcılar bu alanı görmez
    website = forms.CharField(required=False, widget=forms.TextInput(attrs={"tabindex": "-1", "autocomplete": "off"}))

    class Meta:
        model = ContactMessage
        fields = ["name", "email", "phone", "company", "service", "message", "consent"]
        widgets = {
            "message": forms.Textarea(attrs={"rows": 5}),
        }

    def __init__(self, *args, services=None, **kwargs):
        super().__init__(*args, **kwargs)
        names = [s.title for s in services] if services is not None else []
        self.fields["service"] = forms.ChoiceField(
            required=False, choices=[("", "—")] + [(n, n) for n in names] + [("Diğer", "Diğer")]
        )
        self.fields["consent"].required = True
        for name, field in self.fields.items():
            field.widget.attrs.setdefault("id", f"cf-{name}")

    def is_bot(self):
        return bool(self.data.get("website"))


class SubscribeForm(forms.ModelForm):
    class Meta:
        model = Subscriber
        fields = ["email"]

    def validate_unique(self):
        # Zaten kayıtlıysa hata gösterme; görünümde ele alınır
        pass
