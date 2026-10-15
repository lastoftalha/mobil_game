from django import forms


class ImageWidget(forms.ClearableFileInput):
    template_name = "panel/widgets/image.html"

    def __init__(self, attrs=None):
        attrs = {"accept": "image/*", **(attrs or {})}
        super().__init__(attrs)


class VideoWidget(forms.ClearableFileInput):
    template_name = "panel/widgets/file.html"

    def __init__(self, attrs=None):
        attrs = {"accept": "video/mp4,video/webm", **(attrs or {})}
        super().__init__(attrs)


class RichTextWidget(forms.Textarea):
    template_name = "panel/widgets/richtext.html"

    def __init__(self, attrs=None):
        super().__init__({"rows": 10, **(attrs or {})})


class SwitchWidget(forms.CheckboxInput):
    template_name = "panel/widgets/switch.html"


class ColorWidget(forms.TextInput):
    template_name = "panel/widgets/color.html"


class CodeWidget(forms.Textarea):
    def __init__(self, attrs=None):
        super().__init__({"rows": 8, "class": "input code", "spellcheck": "false", **(attrs or {})})


class CheckboxListWidget(forms.CheckboxSelectMultiple):
    template_name = "panel/widgets/checkbox_list.html"
