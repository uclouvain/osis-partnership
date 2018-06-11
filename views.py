from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Count, Q
from django.db.models.functions import Now
from django.views.generic import ListView, DetailView
from django.views.generic.edit import FormMixin

from partnership.forms import PartnerFilterForm
from partnership.models import Partner, Partnership


class PartnersList(LoginRequiredMixin, FormMixin, ListView):
    context_object_name = 'partners'
    form_class = PartnerFilterForm
    paginate_by = 20
    paginate_orphans = 5
    paginate_neighbours = 4

    def get_template_names(self):
        if self.request.is_ajax():
            return 'partnerships/includes/partners_list_results.html'
        else:
            return 'partnerships/partners_list.html'

    def get_context_data(self, **kwargs):
        context = super(PartnersList, self).get_context_data(**kwargs)
        context['paginate_neighbours'] = self.paginate_neighbours
        return context

    def get_form_kwargs(self):
        kwargs = super(PartnersList, self).get_form_kwargs()
        if self.request.GET:
            kwargs['data'] = self.request.GET
        return kwargs

    def get_ordering(self):
        return self.request.GET.get('ordering', '-created')

    def get_queryset(self):
        queryset = Partner.objects.all().annotate(partnerships_count=Count('partnerships'))
        form = self.get_form()
        if form.is_valid():
            data = form.cleaned_data
            if data['name']:
                queryset = queryset.filter(name__icontains=data['name'])
            if data['partner_type']:
                queryset = queryset.filter(partner_type=data['partner_type'])
            if data['pic_code']:
                queryset = queryset.filter(pic_code__icontains=data['pic_code'])
            if data['is_ies'] is not None:
                queryset = queryset.filter(is_ies=data['is_ies'])
            if data['is_valid'] is not None:
                queryset = queryset.filter(is_valid=data['is_valid'])
            if data['is_actif'] is not None:
                if data['is_actif']:
                    queryset = queryset.filter(
                        (Q(start_date__isnull=True) & Q(end_date__isnull=True))
                        | (Q(start_date__lte=Now()) & Q(end_date__gte=Now()))
                    )
                else:
                    queryset = queryset.filter(Q(start_date__gt=Now()) | Q(end_date__lt=Now()))
            if data['tags']:
                queryset = queryset.filter(tags=data['tags'])
        ordering = self.get_ordering()
        if ordering:
            queryset = queryset.order_by(ordering)
        return queryset


class PartnerDetail(LoginRequiredMixin, DetailView):
    model = Partner
    template_name = 'partnerships/partner_detail.html'
    context_object_name = 'partner'


class PartnershipsList(LoginRequiredMixin, ListView):
    model = Partnership
    template_name = 'partnerships/partnerships_list.html'
    context_object_name = 'partnerships'
