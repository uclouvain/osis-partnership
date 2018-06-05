from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Count
from django.views.generic import ListView, DetailView
from django.views.generic.edit import FormMixin

from partnerships.forms import PartnerFilterForm
from partnerships.models import Partner, Partnership


class PartnersList(LoginRequiredMixin, FormMixin, ListView):
    template_name = 'partnerships/partners_list.html'
    context_object_name = 'partners'
    form_class = PartnerFilterForm

    def get_queryset(self):
        queryset = Partner.objects.all().annotate(partnerships_count=Count('partnerships'))
        return queryset


class PartnerDetail(LoginRequiredMixin, DetailView):
    model = Partner
    template_name = 'partnerships/partner_detail.html'
    context_object_name = 'partner'


class PartnershipsList(LoginRequiredMixin, ListView):
    model = Partnership
    template_name = 'partnerships/partnerships_list.html'
    context_object_name = 'partnerships'
