from django import forms

from accounts.models import User

from .models import Campaign


class CampaignForm(forms.ModelForm):
    class Meta:
        model = Campaign
        fields = ("name", "slug", "description", "cover_image", "players", "is_active")
        widgets = {"description": forms.Textarea(attrs={"rows": 4})}

    def __init__(self, *args: object, **kwargs: object) -> None:
        super().__init__(*args, **kwargs)
        self.fields["players"].queryset = User.objects.filter(role=User.Role.PLAYER)
