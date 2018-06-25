from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.db import transaction
from django.db.models import Count, Q, Prefetch
from django.db.models.functions import Now
from django.shortcuts import redirect, get_object_or_404
from django.views.generic import ListView, DetailView
from django.views.generic.edit import FormMixin, CreateView, UpdateView

from partnership.forms import PartnerFilterForm, PartnerForm, MediaForm, PartnerEntityForm
from partnership.models import Partner, Partnership, PartnerEntity
from partnership.utils import user_is_adri


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
                    'medias',
                )
        )

    def get_context_data(self, **kwargs):
        context = super(PartnerDetailView, self).get_context_data(**kwargs)
        context['can_update_partner'] = self.object.user_can_change(self.request.user)
        context['can_add_entities'] = Partner.user_can_add(self.request.user)
        return context


class PartnerCreateView(LoginRequiredMixin, UserPassesTestMixin, CreateView):
    form_class = PartnerForm
    template_name = 'partnerships/partner_create.html'
    prefix = 'partner'

    def test_func(self):
        return Partner.user_can_add(self.request.user)

    def get_form_kwargs(self):
        kwargs = super(PartnerCreateView, self).get_form_kwargs()
        kwargs['user'] = self.request.user
        return kwargs

    def post(self, request, *args, **kwargs):
        self.object = None
        return super(PartnerCreateView, self).post(request, *args, **kwargs)

    def form_valid(self, form):
        partner = form.save(commit=False)
        partner.author = self.request.user
        partner.save()
        form.save_m2m()
        return redirect(partner)


class PartnerUpdateView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    form_class = PartnerForm
    template_name = 'partnerships/partner_update.html'
    prefix = 'partner'
    queryset = Partner.objects.prefetch_related(
        Prefetch('entities', queryset=PartnerEntity.objects.select_related('address', 'contact_in', 'contact_out')),
    )

    def test_func(self):
        self.object = self.get_object()
        return self.object.user_can_change(self.request.user)

    def get_form_kwargs(self):
        kwargs = super(PartnerCreateView, self).get_form_kwargs()
        kwargs['user'] = self.request.user
        return kwargs


class PartnerEntityFormMixin(FormMixin):
    form_class = PartnerEntityForm

    def dispatch(self, request, *args, **kwargs):
        self.partner = get_object_or_404(Partner, pk=kwargs['partner_pk'])
        return super(PartnerEntityFormMixin, self).dispatch(request, *args, **kwargs)

    def get_queryset(self):
        return self.partner.entities.all()

    def get_template_names(self):
        if self.request.is_ajax():
            return 'partnerships/includes/partner_entity_form.html'
        return self.template_name

    def get_success_url(self):
        return self.partner.get_absolute_url()

    def get_context_data(self, **kwargs):
        context = super(PartnerEntityFormMixin, self).get_context_data(**kwargs)
        context['partner'] = self.partner
        return context

    @transaction.atomic
    def form_valid(self, form):
        entity = form.save(commit=False)
        # We need to set the partner
        #  because the one on the entity is not saved yet
        entity.partner = self.partner
        entity.author = self.request.user
        entity.address.save()
        entity.address_id = entity.address.id
        entity.contact_in.save()
        entity.contact_in_id = entity.contact_in.id
        entity.contact_out.save()
        entity.contact_out_id = entity.contact_out.id
        entity.save()
        form.save_m2m()
        return redirect(self.partner)


class PartnerEntityCreateView(UserPassesTestMixin, PartnerEntityFormMixin, CreateView):
    template_name = 'partnerships/partner_entity_create.html'

    def test_func(self):
        return Partner.user_can_add(self.request.user)


class PartnerEntityUpdateView(UserPassesTestMixin, PartnerEntityFormMixin, UpdateView):
    template_name = 'partnerships/partner_entity_update.html'
    context_object_name = 'partner_entity'

    def test_func(self):
        # FIXME CHECK IF USER IS FACULTY MANAGER AND LINKED TO ENTITY
        return user_is_adri(self.request.user)


class PartnerMediaFormMixin(UserPassesTestMixin, FormMixin):
    form_class = MediaForm

    def dispatch(self, request, *args, **kwargs):
        self.partner = get_object_or_404(Partner, pk=kwargs['partner_pk'])
        return super(PartnerMediaFormMixin, self).dispatch(request, *args, **kwargs)

    def test_func(self):
        return self.partner.user_can_change(self.request.user)

    def get_queryset(self):
        return self.partner.medias.all()

    def get_template_names(self):
        if self.request.is_ajax():
            return 'partnerships/includes/media_form.html'
        return self.template_name

    def get_success_url(self):
        return self.partner.get_absolute_url()

    def get_context_data(self, **kwargs):
        context = super(PartnerMediaFormMixin, self).get_context_data(**kwargs)
        context['partner'] = self.partner
        return context

    @transaction.atomic
    def form_valid(self, form):
        media = form.save(commit=False)
        if media.pk is None:
            media.author = self.request.user
        media.save()
        form.save_m2m()
        self.partner.medias.add(media)
        return redirect(self.partner)


# FIXME Make a more generic view and move it with Media in a more generic app
class PartnerMediaCreateView(LoginRequiredMixin, PartnerMediaFormMixin, CreateView):
    template_name = 'partnerships/partner_media_create.html'


# FIXME Make a more generic view and move it with Media in a more generic app
class PartnerMediaUpdateView(LoginRequiredMixin, PartnerMediaFormMixin, UpdateView):
    template_name = 'partnerships/partner_media_update.html'
    context_object_name = 'media'


class PartnershipsList(LoginRequiredMixin, ListView):
    model = Partnership
    template_name = 'partnerships/partnerships_list.html'
    context_object_name = 'partnerships'
