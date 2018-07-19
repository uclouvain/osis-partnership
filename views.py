from dal import autocomplete
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.contrib.postgres.aggregates import StringAgg
from django.core.exceptions import ValidationError
from django.db import transaction
from django.db.models import Count, Prefetch, Q, QuerySet
from django.db.models.functions import Now
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse_lazy
from django.utils.timezone import now
from django.utils.translation import ugettext_lazy as _, ugettext
from django.views import View
from django.views.generic import DetailView, ListView
from django.views.generic.edit import (CreateView, DeleteView, FormMixin,
                                       UpdateView)
from django.views.generic.list import MultipleObjectMixin

from base.models.education_group_year import EducationGroupYear
from base.models.entity_version import EntityVersion
from base.models.person import Person
from osis_common.document import xls_build
from partnership.forms import (AddressForm, MediaForm, PartnerEntityForm,
                               PartnerFilterForm, PartnerForm,
                               PartnershipFilterForm, PartnershipForm,
                               ContactForm, PartnershipAgreementForm, PartnershipYearInlineFormset,
                               PartnershipConfigurationForm)
from partnership.models import Partner, PartnerEntity, Partnership, PartnershipYear, PartnershipAgreement, \
    PartnershipConfiguration
from partnership.utils import user_is_adri


class PartnersListFilterMixin(FormMixin, MultipleObjectMixin):
    form_class = PartnerFilterForm

    def get_form_kwargs(self):
        kwargs = super(PartnersListFilterMixin, self).get_form_kwargs()
        if self.request.GET:
            kwargs['data'] = self.request.GET
        return kwargs

    def filter_queryset(self, queryset):
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
        return queryset

    def get_ordering(self):
        return self.request.GET.get('ordering', '-created')

    def get_queryset(self):
        queryset = (
            Partner.objects
                .all()
                .select_related('partner_type', 'contact_address__country')
                .annotate(partnerships_count=Count('partnerships'))
        )
        queryset = self.filter_queryset(queryset)
        ordering = self.get_ordering()
        if ordering:
            queryset = queryset.order_by(ordering)
        return queryset


class PartnersListView(LoginRequiredMixin, PartnersListFilterMixin, ListView):
    context_object_name = 'partners'
    paginate_by = 20
    paginate_orphans = 2
    paginate_neighbours = 4

    def get_template_names(self):
        if self.request.is_ajax():
            return 'partnerships/partners/includes/partners_list_results.html'
        else:
            return 'partnerships/partners/partners_list.html'

    def get_context_data(self, **kwargs):
        context = super(PartnersListView, self).get_context_data(**kwargs)
        context['paginate_neighbours'] = self.paginate_neighbours
        context['can_add_partner'] = Partner.user_can_add(self.request.user)
        return context


class PartnersExportView(LoginRequiredMixin, PartnersListFilterMixin, View):

    def get_queryset(self):
        queryset = (
            Partner.objects
                .all()
                .select_related('partner_type', 'contact_address__country')
                .annotate(partnerships_count=Count('partnerships'))
        )
        queryset = self.filter_queryset(queryset)
        ordering = self.get_ordering()
        if ordering:
            queryset = queryset.order_by(ordering)
        return queryset

    def get_xls_headers(self):
        return [
            ugettext('id'),
            ugettext('external_id'),
            ugettext('author'),
            ugettext('created'),
            ugettext('changed'),
            ugettext('Name'),
            ugettext('is_valid'),
            ugettext('partner_start_date'),
            ugettext('partner_end_date'),
            ugettext('now_known_as'),
            ugettext('partner_type'),
            ugettext('partner_code'),
            ugettext('pic_code'),
            ugettext('erasmus_code'),
            ugettext('is_ies'),
            ugettext('is_nonprofit'),
            ugettext('is_public'),
            ugettext('use_egracons'),
            ugettext('Name'),
            ugettext('address'),
            ugettext('postal_code'),
            ugettext('city'),
            ugettext('country'),
            ugettext('phone'),
            ugettext('website'),
            ugettext('email'),
            ugettext('contact_type'),
            ugettext('comment'),
            ugettext('tags'),
        ]

    def get_xls_data(self):
        contact_types = dict(Partner.CONTACT_TYPE_CHOICES)
        queryset = self.get_queryset()
        queryset = (
            queryset
            .annotate(tags_list=StringAgg('tags__value', ', '))
            .values_list(
                'id',
                'external_id',
                'author__username',
                'created',
                'changed',
                'name',
                'is_valid',
                'start_date',
                'end_date',
                'now_known_as__name',
                'partner_type__value',
                'partner_code',
                'pic_code',
                'erasmus_code',
                'is_ies',
                'is_nonprofit',
                'is_public',
                'use_egracons',
                'contact_address__name',
                'contact_address__address',
                'contact_address__postal_code',
                'contact_address__city',
                'contact_address__country__name',
                'phone',
                'website',
                'email',
                'contact_type',
                'comment',
                'tags_list',
            )
        )
        for partner in queryset:
            partner = list(partner)
            partner[26] = contact_types.get(partner[26], partner[26])
            yield partner

    def get_xls_filters(self):
        form = self.get_form()
        if form.is_valid():
            filters = {}
            for key, value in form.cleaned_data.items():
                if not value:
                    continue
                if isinstance(value, QuerySet):
                    value = ', '.join(map(str, list(value)))
                filters[key] = str(value)
            return filters
        return None

    def generate_xls(self):
        working_sheets_data = self.get_xls_data()
        parameters = {
            xls_build.DESCRIPTION: _('partners'),
            xls_build.USER: str(self.request.user),
            xls_build.FILENAME: now().strftime('partners-%Y-%m-%d-%H-%m-%S'),
            xls_build.HEADER_TITLES: self.get_xls_headers(),
            xls_build.WS_TITLE: _('partners')
        }
        filters = self.get_xls_filters()
        response = xls_build.generate_xls(
            xls_build.prepare_xls_parameters_list(working_sheets_data, parameters),
            filters,
        )
        return response

    def get(self, request, *args, **kwargs):
        return self.generate_xls()


class PartnerDetailView(LoginRequiredMixin, DetailView):
    template_name = 'partnerships/partners/partner_detail.html'
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


class PartnerFormMixin(object):
    def get_form_kwargs(self):
        kwargs = super(PartnerFormMixin, self).get_form_kwargs()
        kwargs['user'] = self.request.user
        return kwargs

    def get_address_form(self):
        kwargs = {
            'prefix': 'contact_address',
        }
        if self.request.method in ('POST', 'PUT'):
            kwargs['data'] = self.request.POST
        if self.object is not None:
            kwargs['instance'] = self.object.contact_address
        form = AddressForm(**kwargs)
        form.fields['name'].help_text = _('mandatory_if_not_pic_ies')
        form.fields['city'].help_text = _('mandatory_if_not_pic_ies')
        form.fields['country'].help_text = _('mandatory_if_not_pic_ies')
        return form

    def get_context_data(self, **kwargs):
        if 'form_address' not in kwargs:
            kwargs['form_address'] = self.get_address_form()
        kwargs['user_is_adri'] =  user_is_adri(self.request.user)
        return super(PartnerFormMixin, self).get_context_data(**kwargs)

    @transaction.atomic
    def form_valid(self, form, form_address):
        contact_address = form_address.save()
        partner = form.save(commit=False)
        if partner.pk is None:
            partner.author = self.request.user
        partner.contact_address = contact_address
        partner.save()
        form.save_m2m()
        messages.success(self.request, _('partner_saved'))
        return redirect(partner)

    def form_invalid(self, form, form_address):
        messages.error(self.request, _('partner_error'))
        return self.render_to_response(self.get_context_data(
            form=form,
            form_address=form_address
        ))

    def check_form_address(self, form, form_address):
        """ Return True if the conditional mandatory form are ok """
        if not form_address.is_valid():
            return False
        if form.cleaned_data['pic_code'] or form.cleaned_data['is_ies']:
            return True
        cleaned_data = form_address.cleaned_data
        if not cleaned_data['name']:
            form_address.add_error('name', ValidationError(_('required')))
        if not cleaned_data['city']:
            form_address.add_error('city', ValidationError(_('required')))
        if not cleaned_data['country']:
            form_address.add_error('country', ValidationError(_('required')))
        return form_address.is_valid()

    def post(self, request, *args, **kwargs):
        form = self.get_form()
        form_address = self.get_address_form()
        form_valid = form.is_valid()
        form_address_valid = self.check_form_address(form, form_address)
        if form_valid and form_address_valid:
            return self.form_valid(form, form_address)
        else:
            return self.form_invalid(form, form_address)


class PartnerCreateView(LoginRequiredMixin, UserPassesTestMixin, PartnerFormMixin, CreateView):
    form_class = PartnerForm
    template_name = 'partnerships/partners/partner_create.html'
    prefix = 'partner'
    initial = {
        'is_valid': True,
    }

    def test_func(self):
        return Partner.user_can_add(self.request.user)

    def post(self, request, *args, **kwargs):
        self.object = None
        return super(PartnerCreateView, self).post(request, *args, **kwargs)


class PartnerUpdateView(LoginRequiredMixin, UserPassesTestMixin, PartnerFormMixin, UpdateView):
    form_class = PartnerForm
    template_name = 'partnerships/partners/partner_update.html'
    prefix = 'partner'
    queryset = Partner.objects.select_related('contact_address')
    context_object_name = 'partner'

    def test_func(self):
        self.object = self.get_object()
        return self.object.user_can_change(self.request.user)

    def post(self, request, *args, **kwargs):
        self.object = self.get_object()
        return super(PartnerUpdateView, self).post(request, *args, **kwargs)


class SimilarPartnerView(ListView):
    template_name = 'partnerships/partners/includes/similar_partners_preview.html'
    context_object_name = 'similar_partners'

    def get_queryset(self):
        search = self.request.GET.get('search', '')
        # Don't query for small searches
        if len(search) < 3:
            return Partner.objects.none()
        return Partner.objects.filter(name__icontains=search)[:10]


class PartnerEntityMixin(object):
    def dispatch(self, request, *args, **kwargs):
        self.partner = get_object_or_404(Partner, pk=kwargs['partner_pk'])
        return super(PartnerEntityMixin, self).dispatch(request, *args, **kwargs)

    def get_queryset(self):
        return self.partner.entities.all()

    def get_success_url(self):
        return self.partner.get_absolute_url()

    def get_context_data(self, **kwargs):
        context = super(PartnerEntityMixin, self).get_context_data(**kwargs)
        context['partner'] = self.partner
        return context


class PartnerEntityFormMixin(PartnerEntityMixin, FormMixin):
    form_class = PartnerEntityForm

    def get_template_names(self):
        if self.request.is_ajax():
            return 'partnerships/includes/partner_entity_form.html'
        return self.template_name

    def get_form_kwargs(self):
        kwargs = super(PartnerEntityFormMixin, self).get_form_kwargs()
        kwargs['partner'] = self.partner
        return kwargs

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
        messages.success(self.request, _('partner_entity_saved'))
        return redirect(self.partner)

    def form_invalid(self, form):
        messages.error(self.request, _('partner_entity_error'))
        return super(PartnerEntityFormMixin, self).form_invalid(form)


class PartnerEntityCreateView(LoginRequiredMixin, PartnerEntityFormMixin, UserPassesTestMixin, CreateView):
    template_name = 'partnerships/partners/entities/partner_entity_create.html'

    def test_func(self):
        return Partner.user_can_add(self.request.user)


class PartnerEntityUpdateView(LoginRequiredMixin, PartnerEntityFormMixin, UserPassesTestMixin, UpdateView):
    template_name = 'partnerships/partners/entities/partner_entity_update.html'
    context_object_name = 'partner_entity'

    def test_func(self):
        return self.get_object().user_can_change(self.request.user)


class PartnerEntityDeleteView(LoginRequiredMixin, PartnerEntityMixin, DeleteView):
    template_name = 'partnerships/partners/entities/partner_entity_delete.html'

    def test_func(self):
        return self.get_object().user_can_delete(self.request.user)

    def get_template_names(self):
        if self.request.is_ajax():
            return 'partnerships/includes/partner_entity_delete.html'
        return self.template_name


class PartnerMediaMixin(UserPassesTestMixin):

    def dispatch(self, request, *args, **kwargs):
        self.partner = get_object_or_404(Partner, pk=kwargs['partner_pk'])
        return super(PartnerMediaMixin, self).dispatch(request, *args, **kwargs)

    def test_func(self):
        return self.partner.user_can_change(self.request.user)

    def get_queryset(self):
        return self.partner.medias.all()

    def get_success_url(self):
        return self.partner.get_absolute_url()

    def get_context_data(self, **kwargs):
        context = super(PartnerMediaMixin, self).get_context_data(**kwargs)
        context['partner'] = self.partner
        return context


class PartnerMediaFormMixin(PartnerMediaMixin, FormMixin):
    form_class = MediaForm

    def get_template_names(self):
        if self.request.is_ajax():
            return 'partnerships/includes/media_form.html'
        return self.template_name

    @transaction.atomic
    def form_valid(self, form):
        media = form.save(commit=False)
        if media.pk is None:
            media.author = self.request.user
        media.save()
        form.save_m2m()
        self.partner.medias.add(media)
        messages.success(self.request, _('partner_media_saved'))
        return redirect(self.partner)

    def form_invalid(self, form):
        messages.error(self.request, _('partner_media_error'))
        return super(PartnerMediaFormMixin, self).form_invalid(form)


class PartnerMediaCreateView(LoginRequiredMixin, PartnerMediaFormMixin, CreateView):
    template_name = 'partnerships/partners/medias/partner_media_create.html'


class PartnerMediaUpdateView(LoginRequiredMixin, PartnerMediaFormMixin, UpdateView):
    template_name = 'partnerships/partners/medias/partner_media_update.html'
    context_object_name = 'media'


class PartnerMediaDeleteView(LoginRequiredMixin, PartnerMediaMixin, DeleteView):
    template_name = 'partnerships/partners/medias/partner_media_delete.html'

    def get_template_names(self):
        if self.request.is_ajax():
            return 'partnerships/includes/media_delete.html'
        return self.template_name


class PartnershipContactMixin(UserPassesTestMixin):

    def test_func(self):
        return self.partnership.user_can_change(self.request.user)

    def dispatch(self, request, *args, **kwargs):
        self.partnership = get_object_or_404(Partnership, pk=kwargs['partnership_pk'])
        return super(PartnershipContactMixin, self).dispatch(request, *args, **kwargs)

    def get_queryset(self):
        return self.partnership.contacts.all()

    def get_success_url(self):
        return self.partnership.get_absolute_url()

    def get_context_data(self, **kwargs):
        context = super(PartnershipContactMixin, self).get_context_data(**kwargs)
        context['partnership'] = self.partnership
        return context

    
class PartnershipContactFormMixin(PartnershipContactMixin, FormMixin):

    form_class = ContactForm
    
    def get_template_names(self):
        if self.request.is_ajax():
            return 'partnerships/contacts/includes/partnership_contact_form.html'
        return self.template_name

    def form_invalid(self, form):
        messages.error(self.request, _('partner_error'))
        return self.render_to_response(self.get_context_data(
            form=form,
        ))


class PartnershipContactCreateView(PartnershipContactFormMixin, CreateView):

    template_name = 'partnerships/contacts/partnership_contact_create.html'
    
    def form_valid(self, form):
        contact = form.save()
        self.partnership.contacts.add(contact)
        messages.success(self.request, _("contact_creation_success"))
        return redirect(self.partnership)

    
class PartnershipContactUpdateView(PartnershipContactFormMixin, UpdateView):

    template_name = 'partnerships/contacts/partnership_contact_update.html'


class PartnershipContactDeleteView(PartnershipContactMixin, DeleteView):

    template_name = 'partnerships/contacts/contact_confirm_delete.html'
        
    
class PartnershipsListView(LoginRequiredMixin, FormMixin, ListView):
    model = Partnership
    template_name = 'partnerships/partnerships_list.html'
    context_object_name = 'partnerships'
    form_class = PartnershipFilterForm
    paginate_by = 20
    paginate_orphans = 2
    paginate_neighbours = 4

    def get_template_names(self):
        if self.request.is_ajax():
            return 'partnerships/includes/partnerships_list_results.html'
        else:
            return 'partnerships/partnerships_list.html'

    def get_context_data(self, **kwargs):
        context = super(PartnershipsListView, self).get_context_data(**kwargs)
        context['paginate_neighbours'] = self.paginate_neighbours
        context['can_change_configuration'] = user_is_adri(self.request.user)
        context['can_add_partnership'] = Partnership.user_can_add(self.request.user)
        return context

    def get_form_kwargs(self):
        kwargs = super(PartnershipsListView, self).get_form_kwargs()
        if self.request.GET:
            kwargs['data'] = self.request.GET
        return kwargs

    def get_ordering(self):
        ordering = self.request.GET.get('ordering', 'country')
        if ordering == 'country':
            return ['ucl_university__country', 'ucl_university__city', 'partner__name']
        elif ordering == '-country':
            return ['-ucl_university__country', '-ucl_university__city', '-partner__name']
        elif ordering == 'ucl':
            return [
                'ucl_university__entitiversion__parent__entityversion__acronym',
                'ucl_university__entitiversion__acronym',
                'ucl_university_labo__entitiversion__acronym',
            ]
        elif ordering == '-ucl':
            return [
                '-ucl_university__entitiversion__parent__entityversion__acronym',
                '-ucl_university__entitiversion__acronym',
                '-ucl_university_labo__entitiversion__acronym',
            ]
        else:
            return [ordering]

    def get_queryset(self):
        queryset = (
            Partnership.objects
            .all()
            .select_related('ucl_university_labo', 'ucl_university', 'partner', 'partner_entity')
            .prefetch_related(
                Prefetch('university_offers', queryset=EducationGroupYear.objects.select_related('academic_year')),
            )
            .annotate(university_offers_count=Count('university_offers'))
        )
        form = self.get_form()
        if form.is_valid():
            data = form.cleaned_data
            if data['ucl_university']:
                queryset = queryset.filter(ucl_university=data['ucl_university'])
            if data['ucl_university_labo']:
                queryset = queryset.filter(ucl_university_labo=data['ucl_university_labo'])
            if data['university_offers']:
                queryset = queryset.filter(university_offers=data['university_offers'])
            if data['partner']:
                queryset = queryset.filter(partner=data['partner'])
            if data['partner_entity']:
                queryset = queryset.filter(partner__entities=data['partner_entity'])
            if data['partner_type']:
                queryset = queryset.filter(partner__partner_type=data['partner_type'])
            if data['city']:
                queryset = queryset.filter(partner__contact_address__city__icontains=data['city'])
            if data['country']:
                queryset = queryset.filter(partner__contact_address__country=data['country'])
            if data['continent']:
                queryset = queryset.filter(partner__contact_address__country__continent=data['continent'])
            if data['partner_tags']:
                queryset = queryset.filter(partner__tags__in=data['partner_tags'])
            if data['is_sms'] is not None:
                queryset = queryset.filter(years__is_sms=data['is_sms'])
            if data['is_smp'] is not None:
                queryset = queryset.filter(years__is_smp=data['is_smp'])
            if data['is_sta'] is not None:
                queryset = queryset.filter(years__is_sta=data['is_sta'])
            if data['is_stt'] is not None:
                queryset = queryset.filter(years__is_stt=data['is_stt'])
            if data['partnership_type']:
                queryset = queryset.filter(partnership_type=data['partnership_type'])
            if data['tags']:
                queryset = queryset.filter(tags__in=data['tags'])
        ordering = self.get_ordering()
        queryset = queryset.order_by(*ordering)
        return queryset


class PartnershipDetailView(LoginRequiredMixin, DetailView):
    model = Partnership
    context_object_name = 'partnership'
    template_name = 'partnerships/partnership_detail.html'

    def get_context_data(self, **kwargs):
        context = super(PartnershipDetailView, self).get_context_data(**kwargs)
        context['can_change'] = context['object'].user_can_change(self.request.user)
        return context

    def get_object(self):
        self.partnership = (
            Partnership.objects
            .select_related('partner', 'partner_entity', 'ucl_university', 'ucl_university_labo', 'author')
            .prefetch_related(
                'contacts',
                'tags',
                Prefetch('university_offers', queryset=EducationGroupYear.objects.select_related('academic_year')),
                Prefetch('years', queryset=PartnershipYear.objects.select_related('academic_year')),
                Prefetch('agreements', queryset=PartnershipAgreement.objects.select_related(
                    'start_academic_year', 'end_academic_year', 'media'
                )),
            )
            .annotate(university_offers_count=Count('university_offers'))
            .get(pk=self.kwargs['pk'])
        )
        return self.partnership


class PartnershipFormMixin(object):

    model = Partnership
    form_class = PartnershipForm

    def get_formset_years(self):
        kwargs = self.get_form_kwargs()
        kwargs['prefix'] = 'years'
        return PartnershipYearInlineFormset(**kwargs)

    def get_context_data(self, **kwargs):
        if 'formset_years' not in kwargs:
            kwargs['formset_years'] = self.get_formset_years()
        return super(PartnershipFormMixin, self).get_context_data(**kwargs)

    def form_invalid(self, form, formset_years):
        messages.error(self.request, _('partnership_error'))
        return self.render_to_response(self.get_context_data(form=form, formset_years=formset_years))

    def post(self, request, *args, **kwargs):
        form = self.get_form()
        formset_years = self.get_formset_years()
        # Do the valid before to ensure the errors are calculated
        formset_years_valid = formset_years.is_valid()
        if form.is_valid() and formset_years_valid:
            return self.form_valid(form, formset_years)
        else:
            return self.form_invalid(form, formset_years)


class PartnershipCreateView(LoginRequiredMixin, UserPassesTestMixin, PartnershipFormMixin, CreateView):

    model = Partnership
    form_class = PartnershipForm
    template_name = "partnerships/partnership_create.html"

    def test_func(self):
        return Partnership.user_can_add(self.request.user)

    @transaction.atomic
    def form_valid(self, form, formset_years):
        partnership = form.save(commit=False)
        partnership.author = self.request.user
        partnership.save()
        form.save_m2m()
        formset_years.instance = partnership
        formset_years.save()
        messages.success(self.request, _('partnership_success'))
        return redirect(partnership)

    def post(self, request, *args, **kwargs):
        self.object = None
        return super(PartnershipCreateView, self).post(request, *args, **kwargs)


class PartnershipUpdateView(LoginRequiredMixin, UserPassesTestMixin, PartnershipFormMixin, UpdateView):

    model = Partnership
    form_class = PartnershipForm
    template_name = "partnerships/partnership_update.html"

    def test_func(self):
        return self.object.user_can_change(self.request.user)

    @transaction.atomic
    def form_valid(self, form, formset_years):
        partnership = form.save()
        formset_years.save()
        messages.success(self.request, _('partnership_success'))
        return redirect(partnership)

    def post(self, request, *args, **kwargs):
        self.object = self.get_object()
        return super(PartnershipUpdateView, self).post(request, *args, **kwargs)


class PartnershipAgreementsMixin(UserPassesTestMixin):
    context_object_name = 'agreement'

    def test_func(self):
        return self.partnership.user_can_change(self.request.user)

    def dispatch(self, request, *args, **kwargs):
        self.partnership = get_object_or_404(Partnership, pk=kwargs['partnership_pk'])
        return super(PartnershipAgreementsMixin, self).dispatch(request, *args, **kwargs)

    def get_queryset(self):
        return self.partnership.agreements.all()

    def get_success_url(self):
        return self.partnership.get_absolute_url()

    def get_context_data(self, **kwargs):
        context = super(PartnershipAgreementsMixin, self).get_context_data(**kwargs)
        context['partnership'] = self.partnership
        return context


class PartnershipAgreementsFormMixin(PartnershipAgreementsMixin):
    form_class = PartnershipAgreementForm

    def get_template_names(self):
        if self.request.is_ajax():
            return 'partnerships/includes/partnership_agreement_form.html'
        return self.template_name

    def get_form_kwargs(self):
        kwargs = super(PartnershipAgreementsFormMixin, self).get_form_kwargs()
        kwargs['user'] = self.request.user
        return kwargs

    def get_form_media(self):
        kwargs = self.get_form_kwargs()
        kwargs['prefix'] = 'media'
        if self.object is not None:
            kwargs['instance'] = self.object.media
        del kwargs['user']
        return MediaForm(**kwargs)

    def get_context_data(self, **kwargs):
        if 'form_media' not in kwargs:
            kwargs['form_media'] = self.get_form_media()
        return super(PartnershipAgreementsFormMixin, self).get_context_data(**kwargs)

    def form_invalid(self, form, form_media):
        messages.error(self.request, _('partnership_agreement_error'))
        return self.render_to_response(self.get_context_data(form=form, form_media=form_media))

    def post(self, request, *args, **kwargs):
        form = self.get_form()
        form_media = self.get_form_media()
        # Do the valid before to ensure the errors are calculated
        form_media_valid = form_media.is_valid()
        if form.is_valid() and form_media_valid:
            return self.form_valid(form, form_media)
        else:
            return self.form_invalid(form, form_media)


class PartneshipAgreementCreateView(PartnershipAgreementsFormMixin, CreateView):
    template_name = 'partnerships/agreements/create.html'

    @transaction.atomic
    def form_valid(self, form, form_media):
        media = form_media.save(commit=False)
        media.author = self.request.user
        media.save()
        form_media.save_m2m()
        agreement = form.save(commit=False)
        agreement.partnership = self.partnership
        agreement.media = media
        agreement.save()
        form.save_m2m()
        messages.success(self.request, _('partnership_agreement_success'))
        return redirect(self.partnership)

    def post(self, request, *args, **kwargs):
        self.object = None
        return super(PartneshipAgreementCreateView, self).post(request, *args, **kwargs)


class PartneshipAgreementUpdateView(PartnershipAgreementsFormMixin, UpdateView):
    template_name = 'partnerships/agreements/update.html'

    @transaction.atomic
    def form_valid(self, form, form_media):
        form_media.save()
        form.save()
        messages.success(self.request, _('partnership_agreement_success'))
        return redirect(self.partnership)

    def post(self, request, *args, **kwargs):
        self.object = self.get_object()
        return super(PartneshipAgreementUpdateView, self).post(request, *args, **kwargs)


class PartneshipAgreementDeleteView(LoginRequiredMixin, PartnershipAgreementsMixin, DeleteView):
    template_name = 'partnerships/agreements/delete.html'

    def get_template_names(self):
        if self.request.is_ajax():
            return 'partnerships/agreements/includes/delete.html'
        return self.template_name


class PartneshipConfigurationUpdateView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    form_class = PartnershipConfigurationForm
    template_name = 'partnerships/configuration_update.html'
    success_url = reverse_lazy('partnerships:partnerships_list')

    def test_func(self):
        return user_is_adri(self.request.user)

    def get_object(self, queryset=None):
        return PartnershipConfiguration.get_configuration()


### Autocompletes

class PersonAutocompleteView(autocomplete.Select2QuerySetView):

    def get_queryset(self):
        qs = Person.objects
        if self.q:
            qs = qs.filter(
                Q(first_name__icontains=self.q) |
                Q(middle_name__icontains=self.q) |
                Q(last_name__icontains=self.q)
            )
        return qs


class UclUniversityAutocompleteView(autocomplete.Select2QuerySetView):
    
    def get_queryset(self):
        if not self.request.user.is_authenticated():
            return EntityVersion.objects.none()

        qs = EntityVersion.objects.all()
        if self.q:
            qs = qs.filter(acronym__icontains=self.q)

        return qs


class UclUniversityAutocompleteFilterView(UclUniversityAutocompleteView):

    def get_queryset(self):
        qs = super().get_queryset()
        return qs.filter(partnerships__isnull=False)

    
class UclUniversityLaboAutocompleteFilterView(UclUniversityAutocompleteView):

    def get_queryset(self):
        qs = super().get_queryset()
        ucl_university = self.forwarded.get('ucl_university', None)
        if ucl_university:
            qs = qs.filter(partnerships_labo__ucl_university=ucl_university)
        return qs.filter(partnerships_labo__isnull=False)


class UniversityOffersAutocompleteView(autocomplete.Select2QuerySetView):

    def get_queryset(self):
        if not self.request.user.is_authenticated():
            return EducationGroupYear.objects.none()

        qs = EducationGroupYear.objects.all().select_related('academic_year')
        if self.q:
            qs = qs.filter(title__icontains=self.q)

        return qs


class UniversityOffersAutocompleteFilterView(UniversityOffersAutocompleteView):

    def get_queryset(self):
        qs = super().get_queryset()
        ucl_university = self.forwarded.get('ucl_university', None)
        if ucl_university:
            qs = qs.filter(partnerships__ucl_university=ucl_university)
        return qs.filter(partnerships__isnull=False)
