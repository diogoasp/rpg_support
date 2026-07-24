from django import forms
from django.contrib.auth.forms import PasswordChangeForm


class RequiredPasswordChangeForm(PasswordChangeForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs.update({"class": "form-control form-control-lg"})

    def clean(self):
        cleaned_data = super().clean()
        password = cleaned_data.get("new_password2")
        if password and self.user.check_password(password):
            self.add_error("new_password2", forms.ValidationError("A nova senha deve ser diferente da senha atual."))
        return cleaned_data
