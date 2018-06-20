from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.db import transaction
from django.db.models import Count, Q, Prefetch
from django.db.models.functions import Now
from django.shortcuts import redirect
from django.views.generic import ListView, DetailView
from django.views.generic.edit import FormMixin, CreateView

from partnership.forms import PartnerFilterForm, PartnerForm, PartnerEntitiesFormset
from partnership.models import Partner, Partnership, Media, PartnerEntity


class IsAdriOrGfMixin(UserPassesTestMixin):

    def test_func(self):
        return Partner.user_can_add(self.request.user)


class PartnersListView(LoginRequiredMixin, FormMixin, ListView):
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
        context = super(PartnersListView, self).get_context_data(**kwargs)
        context['paginate_neighbours'] = self.paginate_neighbours
        context['can_add_partner'] = Partner.user_can_add(self.request.user)
        return context

    def get_form_kwargs(self):
        kwargs = super(PartnersListView, self).get_form_kwargs()
        if self.request.GET:
            kwargs['data'] = self.request.GET
        return kwargs

    def get_ordering(self):
        return self.request.GET.get('ordering', '-created')

    def get_queryset(self):
        queryset = (
            Partner.objects
                .all()
                .select_related('partner_type', 'contact_address__country')
                .annotate(partnerships_count=Count('partnerships'))
        )
        form = self.get_form()
        if form.is_valid():
            data = form.cleaned_data
            if data['name']:
                queryset = queryset.filter(name__icontains=data['name'])
            if data['partner_type']:
                queryset = queryset.filter(partner_type=data['partner_type'])
            if data['pic_code']:
                queryset = queryset.filter(pic_code__icontains=data['pic_code'])
            if data['erasmus_code']:
                queryset = queryset.filter(erasmus_code__icontains=data['erasmus_code'])
            if data['city']:
                queryset = queryset.filter(contact_address__city__icontains=data['city'])
            if data['country']:
                queryset = queryset.filter(contact_address__country=data['country'])
            if data['continent']:
                queryset = queryset.filter(contact_address__country__continent=data['continent'])
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
                queryset = queryset.filter(tags__in=data['tags'])
        ordering = self.get_ordering()
        if ordering:
            queryset = queryset.order_by(ordering)
        return queryset


class PartnerDetailView(LoginRequiredMixin, DetailView):
    template_name = 'partnerships/partner_detail.html'
    context_object_name = 'partner'

    def get_queryset(self):
        return (
            Partner.objects
                .select_related('partner_type', 'author')
                .prefetch_related(
                    Prefetch('entities', queryset=PartnerEntity.objects.select_related(
                        'contact_in', 'contact_out', 'address', 'parent', 'author',
                    )),
                    'tags',
                    Prefetch('medias', queryset=Media.objects.select_related('document_file')),
                )
        )


class PartnerCreateView(LoginRequiredMixin, IsAdriOrGfMixin, CreateView):
    form_class = PartnerForm
    template_name = 'partnerships/partner_create.html'
    prefix = 'partner'

    def get_entities_formset(self):
        kwargs = self.get_form_kwargs()
        kwargs['prefix'] = 'entities'
        return PartnerEntitiesFormset(**kwargs)

    def get_context_data(self, **kwargs):
        if 'entities_formset' not in kwargs:
            kwargs['entities_formset'] = self.get_entities_formset()
        return super(PartnerCreateView, self).get_context_data(**kwargs)

    def post(self, request, *args, **kwargs):
        self.object = None
        form = self.get_form()
        entities_formset = self.get_entities_formset()
        if form.is_valid() and entities_formset.is_valid():
            return self.form_valid(form, entities_formset)
        else:
            return self.form_invalid(form, entities_formset)

    @transaction.atomic
    def form_valid(self, form, entities_formset):
        partner = form.save(commit=False)
        partner.author = self.request.user
        partner.save()
        entities = entities_formset.save(commit=False)
        # Save one by one to save related models
        for entity in entities:
            # We need to set the partner
            #  because the one on the entity is not saved yet
            entity.partner = partner
            entity.author = self.request.user
            entity.address.save()
            entity.address_id = entity.address.id
            entity.contact_in.save()
            entity.contact_in_id = entity.contact_in.id
            entity.contact_out.save()
            entity.contact_out_id = entity.contact_out.id
            entity.save()
        entities_formset.save_m2m()
        form.save_m2m()
        return redirect(partner)

    def form_invalid(self, form, entities_formset):
        return self.render_to_response(self.get_context_data(
            form=form,
            entities_formset=entities_formset,
        ))


class PartnershipsList(LoginRequiredMixin, ListView):
    model = Partnership
    template_name = 'partnerships/partnerships_list.html'
    context_object_name = 'partnerships'
