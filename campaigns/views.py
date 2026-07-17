from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.urls import reverse_lazy
from django.views.generic import CreateView, DetailView, UpdateView

from .forms import CampaignForm
from .mixins import CampaignMemberRequiredMixin, MasterRequiredMixin
from .models import Campaign


class CampaignDetailView(CampaignMemberRequiredMixin, DetailView):
    model = Campaign
    template_name = "campaigns/campaign_detail.html"
    slug_url_kwarg = "slug"


class CampaignCreateView(MasterRequiredMixin, CreateView):
    model = Campaign
    form_class = CampaignForm
    template_name = "campaigns/campaign_form.html"

    def form_valid(self, form):
        form.instance.master = self.request.user
        return super().form_valid(form)


class CampaignUpdateView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    model = Campaign
    form_class = CampaignForm
    template_name = "campaigns/campaign_form.html"
    slug_url_kwarg = "slug"

    def test_func(self) -> bool:
        return self.get_object().master_id == self.request.user.pk
