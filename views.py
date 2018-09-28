from copy import copy

from dal import autocomplete
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.contrib.postgres.aggregates import StringAgg
from django.core.exceptions import ValidationError
from django.db import transaction
from django.db.models import (Count, Exists, Max, OuterRef, Prefetch, Q,
                              QuerySet)
from django.db.models.functions import Now
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse_lazy
from django.utils.timezone import now
from django.utils.translation import ugettext
from django.utils.translation import ugettext_lazy as _
from django.views import View
from django.views.generic import DetailView, ListView
from django.views.generic.edit import (CreateView, DeleteView, FormMixin,
                                       UpdateView)
from django.views.generic.list import MultipleObjectMixin

from base.models.academic_year import find_academic_years, current_academic_year
from base.models.education_group_year import EducationGroupYear
from base.models.entity import Entity
from base.models.entity_version import EntityVersion
from base.models.enums.entity_type import FACULTY
from base.models.person import Person
from osis_common.document import xls_build
from partnership.forms import (AddressForm, ContactForm, MediaForm,
                               PartnerEntityForm, PartnerFilterForm,
                               PartnerForm, PartnershipAgreementForm,
                               PartnershipConfigurationForm,
                               PartnershipFilterForm, PartnershipForm,
                               PartnershipYearForm,
                               UCLManagementEntityForm
)
from partnership.models import (Partner, PartnerEntity, Partnership,
                                PartnershipAgreement, PartnershipConfiguration,
                                PartnershipYear, UCLManagementEntity)
from partnership.utils import user_is_adri, user_is_gf


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
            Partner.objects.all()
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
        kwargs['user_is_adri'] = user_is_adri(self.request.user)
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


class PartnerEntityDeleteView(LoginRequiredMixin, PartnerEntityMixin, UserPassesTestMixin, DeleteView):
    template_name = 'partnerships/partners/entities/partner_entity_delete.html'
    context_object_name = 'partner_entity'

    def test_func(self):
        return self.get_object().user_can_delete(self.request.user)

    def get_template_names(self):
        if self.request.is_ajax():
            return 'partnerships/partners/entities/includes/partner_entity_delete.html'
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


class PartnershipContactMixin(LoginRequiredMixin, UserPassesTestMixin):

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

    def get_template_names(self):
        if self.request.is_ajax():
            return 'partnerships/contacts/includes/contact_delete_form.html'
        return self.template_name


class PartnershipListFilterMixin(FormMixin, MultipleObjectMixin):
    form_class = PartnershipFilterForm

    def get_initial(self):
        initial = {}
        if user_is_gf(self.request.user):
            university = self.request.user.person.entitymanager_set.first().entity
            if Partnership.objects.filter(ucl_university=university).exists():
                initial['ucl_university'] = self.request.user.person.entitymanager_set.first().entity
        return initial

    def get_form_kwargs(self):
        kwargs = super(PartnershipListFilterMixin, self).get_form_kwargs()
        if self.request.GET:
            # Remove empty value from GET
            data = copy(self.request.GET)
            for key, value in list(data.items()):
                if value == '':
                    del data[key]
            kwargs['data'] = data
        return kwargs

    def get_ordering(self):
        ordering = self.request.GET.get('ordering', 'country')
        if ordering == 'country':
            return ['partner__contact_address__country__name', 'partner__contact_address__city', 'partner__name']
        elif ordering == '-country':
            return ['-partner__contact_address__country__name', '-partner__contact_address__city', '-partner__name']
        elif ordering == 'ucl':
            return [
                'ucl_university__entityversion__parent__entityversion__acronym',
                'ucl_university__entityversion__acronym',
                'ucl_university_labo__entityversion__acronym',
            ]
        elif ordering == '-ucl':
            return [
                '-ucl_university__entityversion__parent__entityversion__acronym',
                '-ucl_university__entityversion__acronym',
                '-ucl_university_labo__entityversion__acronym',
            ]
        else:
            return [ordering]

    def filter_queryset(self, queryset, data):
        if data.get('ucl_university', None):
            queryset = queryset.filter(ucl_university=data['ucl_university'])
        if data.get('ucl_university_labo', None):
            queryset = queryset.filter(ucl_university_labo=data['ucl_university_labo'])
        if data.get('university_offers', None):
            queryset = queryset.filter(years__offers__in=data['university_offers'])
        if data.get('partner', None):
            queryset = queryset.filter(partner=data['partner'])
        if data.get('partner_entity', None):
            queryset = queryset.filter(partner_entity=data['partner_entity'])
        if data.get('partner_type', None):
            queryset = queryset.filter(partner__partner_type=data['partner_type'])
        if data.get('partner_tags', None):
            queryset = queryset.filter(partner__tags__in=data['partner_tags'])
        if data.get('erasmus_code', None):
            queryset = queryset.filter(partner__erasmus_code__icontains=data['erasmus_code'])
        if data.get('city', None):
            queryset = queryset.filter(partner__contact_address__city__icontains=data['city'])
        if data.get('country', None):
            queryset = queryset.filter(partner__contact_address__country=data['country'])
        if data.get('continent', None):
            queryset = queryset.filter(partner__contact_address__country__continent=data['continent'])
        if data.get('partner_tags', None):
            queryset = queryset.filter(partner__tags__in=data['partner_tags'])
        if data.get('is_sms', None) is not None:
            queryset = queryset.filter(years__is_sms=data['is_sms'])
        if data.get('is_smp', None) is not None:
            queryset = queryset.filter(years__is_smp=data['is_smp'])
        if data.get('is_sta', None) is not None:
            queryset = queryset.filter(years__is_sta=data['is_sta'])
        if data.get('is_stt', None) is not None:
            queryset = queryset.filter(years__is_stt=data['is_stt'])
        if data.get('partnership_type', None):
            queryset = queryset.filter(years__partnership_type=data['partnership_type'])
        if data.get('supervisor', None):
            queryset = queryset.filter(supervisor=data['supervisor'])
        if data.get('education_field', None):
            queryset = queryset.filter(years__education_fields=data['education_field'])
        if data.get('education_level', None):
            queryset = queryset.filter(years__education_levels=data['education_level'])
        if data.get('tags', None):
            queryset = queryset.filter(tags__in=data['tags'])
        if data.get('partnership_in', None):
            partnership_in = data['partnership_in']
            queryset = queryset.annotate(
                has_in=Exists(
                    PartnershipAgreement.objects.filter(
                        partnership=OuterRef('pk'),
                        start_academic_year__start_date__lte=partnership_in.start_date,
                        end_academic_year__end_date__gte=partnership_in.end_date,
                    )
                )
            ).filter(has_in=True)
        if data.get('partnership_ending_in', None):
            partnership_ending_in = data['partnership_ending_in']
            queryset = (
                queryset.annotate(
                    ending_date=Max('agreements__end_academic_year__end_date')
                ).filter(ending_date=partnership_ending_in.end_date)
            )
        if data.get('partnership_valid_in', None):
            partnership_valid_in = data['partnership_valid_in']
            # We need to use subqueries to avoid conflicts with partnership_not_valid_in filter
            queryset = queryset.annotate(
                has_valid=Exists(
                    PartnershipAgreement.objects.filter(
                        partnership=OuterRef('pk'), status=PartnershipAgreement.STATUS_VALIDATED,
                        start_academic_year__start_date__lte=partnership_valid_in.start_date,
                        end_academic_year__end_date__gte=partnership_valid_in.end_date,
                    )
                )
            ).filter(has_valid=True)
        if data.get('partnership_not_valid_in', None):
            # We need to use subqueries to avoid conflicts with partnership_valid_in filter
            partnership_not_valid_in = data['partnership_not_valid_in']
            queryset = queryset.annotate(
                not_valid_in_has_agreements=Exists(
                    PartnershipAgreement.objects.filter(
                        partnership=OuterRef('pk')).filter(
                        start_academic_year__start_date__lte=partnership_not_valid_in.start_date,
                        end_academic_year__end_date__gte=partnership_not_valid_in.end_date), ),
                not_valid_in_has_valid_agreements=Exists(
                    PartnershipAgreement.objects.filter(partnership=OuterRef('pk')).filter(
                        status=PartnershipAgreement.STATUS_VALIDATED,
                        start_academic_year__start_date__lte=partnership_not_valid_in.start_date,
                        end_academic_year__end_date__gte=partnership_not_valid_in.end_date),
                )
            ).filter(not_valid_in_has_agreements=True, not_valid_in_has_valid_agreements=False)
        if data.get('comment', None):
            queryset = queryset.filter(comment__icontains=data['comment'])
        return queryset

    def get_queryset(self):
        queryset = (
            Partnership.objects
            .all()
            .select_related(
                'ucl_university_labo', 'ucl_university',
                'partner__contact_address__country', 'partner_entity',
                'supervisor',
            )
        )
        form = self.get_form()
        if not form.is_bound:
            queryset = self.filter_queryset(queryset, self.get_initial())
        elif form.is_valid():
            queryset = self.filter_queryset(queryset, form.cleaned_data)
        ordering = self.get_ordering()
        queryset = queryset.order_by(*ordering)
        return queryset.distinct()


class PartnershipsListView(LoginRequiredMixin, PartnershipListFilterMixin, ListView):
    template_name = 'partnerships/partnerships_list.html'
    context_object_name = 'partnerships'
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


class PartnershipExportView(LoginRequiredMixin, PartnershipListFilterMixin, View):

    def get_xls_headers(self):
        return [
            ugettext('id'),
            ugettext('partner'),
            ugettext('partner_entity'),
            ugettext('ucl_university'),
            ugettext('ucl_university_labo'),
            ugettext('university_offers'),
            ugettext('supervisor'),
            ugettext('start_date'),
            ugettext('comment'),
            ugettext('tags'),
            ugettext('created'),
            ugettext('modified'),
            ugettext('author'),
        ]

    def get_xls_data(self):
        contact_types = dict(Partner.CONTACT_TYPE_CHOICES)
        queryset = self.get_queryset()
        queryset = (
            queryset
            .annotate(
                tags_list=StringAgg('tags__value', ', '),
            )
            .select_related('author')
            .prefetch_related(
                Prefetch(
                    'ucl_university__entityversion_set',
                    queryset=EntityVersion.objects.order_by('-start_date')
                ),
                Prefetch(
                    'ucl_university_labo__entityversion_set',
                    queryset=EntityVersion.objects.order_by('-start_date')
                ),
            )
        )
        for partnership in queryset:
            yield [
                partnership.pk,
                str(partnership.partner),
                str(partnership.partner_entity) if partnership.partner_entity else None,
                str(partnership.ucl_university.entityversion_set.all()[0]),
                str(partnership.ucl_university_labo.entityversion_set.all()[0]) if partnership.ucl_university_labo else '',
                ', '.join(map(str, partnership.university_offers.all())),
                str(partnership.supervisor) if partnership.supervisor is not None else '',
                partnership.start_date.strftime('%Y-%m-%d'),
                partnership.comment,
                partnership.tags_list,
                partnership.created.strftime('%Y-%m-%d'),
                partnership.modified.strftime('%Y-%m-%d'),
                str(partnership.author),
            ]

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


class PartnershipDetailView(LoginRequiredMixin, DetailView):
    model = Partnership
    context_object_name = 'partnership'
    template_name = 'partnerships/partnership_detail.html'

    def get_context_data(self, **kwargs):
        context = super(PartnershipDetailView, self).get_context_data(**kwargs)
        context['can_change'] = context['object'].user_can_change(self.request.user)
        return context

    def get_object(self):
        return get_object_or_404(
            Partnership.objects
            .select_related(
                'partner', 'partner_entity', 'ucl_university',
                'ucl_university_labo', 'author'
            )
            .prefetch_related(
                'contacts',
                'tags',
                Prefetch(
                    'years',
                    queryset=PartnershipYear.objects.select_related('academic_year')
                ),
                Prefetch('agreements', queryset=PartnershipAgreement.objects.select_related(
                    'start_academic_year', 'end_academic_year', 'media'
                ).order_by("-start_academic_year", "-end_academic_year")),
            ),
            pk=self.kwargs['pk'],
        )


class PartnershipFormMixin(object):

    model = Partnership
    form_class = PartnershipForm

    def get_form_year(self):
        kwargs = self.get_form_kwargs()
        kwargs['prefix'] = 'year'
        partnership = kwargs['instance']
        if partnership is not None:
            kwargs['instance'] = partnership.current_year
            if kwargs['instance'] is None:
                # No current year for this partnership, get the last available
                kwargs['instance'] = partnership.years.last()
        return PartnershipYearForm(**kwargs)

    def get_form_kwargs(self):
        kwargs = super(PartnershipFormMixin, self).get_form_kwargs()
        kwargs['user'] = self.request.user
        return kwargs

    def get_context_data(self, **kwargs):
        if 'form_year' not in kwargs:
            kwargs['form_year'] = self.get_form_year()
        kwargs['current_academic_year'] = current_academic_year()
        return super(PartnershipFormMixin, self).get_context_data(**kwargs)

    def form_invalid(self, form, form_year):
        messages.error(self.request, _('partnership_error'))
        return self.render_to_response(self.get_context_data(form=form, form_year=form_year))

    def post(self, request, *args, **kwargs):
        form = self.get_form()
        form_year = self.get_form_year()
        form_year_is_valid = form_year.is_valid()
        if form.is_valid() and form_year_is_valid:
            return self.form_valid(form, form_year)
        else:
            return self.form_invalid(form, form_year)


class PartnershipCreateView(LoginRequiredMixin, UserPassesTestMixin, PartnershipFormMixin, CreateView):

    model = Partnership
    form_class = PartnershipForm
    template_name = "partnerships/partnership_create.html"

    def test_func(self):
        return Partnership.user_can_add(self.request.user)

    @transaction.atomic
    def form_valid(self, form, form_year):
        partnership = form.save(commit=False)
        partnership.author = self.request.user

        # Resume saving
        partnership.save()
        form.save_m2m()

        # Create years
        start_year = form_year.cleaned_data['start_academic_year'].year
        end_year = form_year.cleaned_data['end_academic_year'].year
        academic_years = find_academic_years(start_year=start_year, end_year=end_year)
        for academic_year in academic_years:
            partnership_year = form_year.save(commit=False)
            partnership_year.id = None  # Force the creation of a new PartnershipYear
            partnership_year.partnership = partnership
            partnership_year.academic_year = academic_year
            partnership_year.save()
            form_year.save_m2m()

        messages.success(self.request, _('partnership_success'))
        return redirect(partnership)

    def post(self, request, *args, **kwargs):
        self.object = None
        return super(PartnershipCreateView, self).post(request, *args, **kwargs)


class PartnershipUpdateView(LoginRequiredMixin, UserPassesTestMixin, PartnershipFormMixin, UpdateView):

    model = Partnership
    form_class = PartnershipForm
    template_name = "partnerships/partnership_update.html"

    def dispatch(self, *args, **kwargs):
        self.object = self.get_object()
        return super().dispatch(*args, **kwargs)

    def test_func(self):
        return self.get_object().user_can_change(self.request.user)

    @transaction.atomic
    def form_valid(self, form, form_year):
        partnership = form.save()

        start_year = form_year.cleaned_data['start_academic_year'].year
        from_year = form_year.cleaned_data['from_academic_year'].year
        end_year = form_year.cleaned_data['end_academic_year'].year

        # Create missing start year if needed
        first_year = partnership.years.order_by('academic_year__year').select_related('academic_year').first()
        first_year_education_fields = first_year.education_fields.all()
        first_year_education_levels = first_year.education_levels.all()
        first_year_entities = first_year.entities.all()
        first_year_offers = first_year.offers.all()
        academic_years = find_academic_years(start_year=start_year, end_year=first_year.academic_year.year - 1)
        for academic_year in academic_years:
            first_year.id = None
            first_year.academic_year = academic_year
            first_year.save()
            first_year.education_fields = first_year_education_fields
            first_year.education_levels = first_year_education_levels
            first_year.entities = first_year_entities
            first_year.offers = first_year_offers

        # Update years
        academic_years = find_academic_years(start_year=from_year, end_year=end_year)
        for academic_year in academic_years:
            partnership_year = form_year.save(commit=False)
            try:
                partnership_year.pk = PartnershipYear.objects.get(
                    partnership=partnership, academic_year=academic_year
                ).pk
            except PartnershipYear.DoesNotExist:
                partnership_year.pk = None
            partnership_year.academic_year = academic_year
            partnership_year.save()
            form_year.save_m2m()

        # Delete no longer used years
        PartnershipYear.objects.filter(partnership=partnership).filter(
            Q(academic_year__year__lt=start_year) | Q(academic_year__year__gt=end_year)
        ).delete()

        messages.success(self.request, _('partnership_success'))
        return redirect(partnership)

    def post(self, request, *args, **kwargs):
        return super(PartnershipUpdateView, self).post(request, *args, **kwargs)


class PartnershipAgreementsMixin(LoginRequiredMixin, UserPassesTestMixin):
    context_object_name = 'agreement'

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

    def test_func(self):
        return self.partnership.user_can_change(self.request.user)

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

    def test_func(self):
        return self.get_object().user_can_change(self.request.user)

    def get_queryset(self):
        return PartnershipAgreement.objects.select_related('start_academic_year', 'end_academic_year')

    @transaction.atomic
    def form_valid(self, form, form_media):
        form_media.save()
        form.save()
        messages.success(self.request, _('partnership_agreement_success'))
        return redirect(self.partnership)

    def post(self, request, *args, **kwargs):
        self.object = self.get_object()
        return super(PartneshipAgreementUpdateView, self).post(request, *args, **kwargs)


class PartneshipAgreementDeleteView(PartnershipAgreementsMixin, DeleteView):
    template_name = 'partnerships/agreements/delete.html'

    def test_func(self):
        return self.get_object().user_can_change(self.request.user)

    def get_template_names(self):
        if self.request.is_ajax():
            return 'partnerships/agreements/includes/delete.html'
        return self.template_name


class PartneshipConfigurationUpdateView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    form_class = PartnershipConfigurationForm
    template_name = 'partnerships/configuration_update.html'
    success_url = reverse_lazy('partnerships:list')

    def test_func(self):
        return user_is_adri(self.request.user)

    def get_object(self, queryset=None):
        return PartnershipConfiguration.get_configuration()

    def form_valid(self, form):
        messages.success(self.request, _('configuration_saved'))
        return super().form_valid(form)


# UCLManagementEntities views :

class UCLManagementEntityListView(LoginRequiredMixin, ListView):
    model = UCLManagementEntity
    template_name = "partnerships/ucl_management_entities/uclmanagemententity_list.html"
    context_object_name = "ucl_management_entities"


class UCLManagementEntityCreateView(LoginRequiredMixin, CreateView):
    model = UCLManagementEntity
    template_name = "partnerships/ucl_management_entities/uclmanagemententity_create.html"
    form_class = UCLManagementEntityForm


class UCLManagementEntityUpdateView(LoginRequiredMixin, UpdateView):
    model = UCLManagementEntity
    template_name = "partnerships/ucl_management_entities/uclmanagemententity_update.html"
    form_class = UCLManagementEntityForm
    context_object_name = "ucl_management_entity"


class UCLManagementEntityDeleteView(LoginRequiredMixin, DeleteView):
    model = UCLManagementEntity
    template_name = "partnerships/ucl_management_entities/uclmanagemententity_delete.html"
    context_object_name = "ucl_management_entity"
    success_url = reverse_lazy('partnerships:ucl_management_entities:list')


class UCLManagementEntityDetailView(LoginRequiredMixin, DetailView):
    model = UCLManagementEntity
    template_name = "partnerships/ucl_management_entities/uclmanagemententity_detail.html"
    context_object_name = "ucl_management_entity"


# Autocompletes

class PersonAutocompleteView(autocomplete.Select2QuerySetView):

    def get_queryset(self):
        qs = Person.objects.all()
        if self.q:
            qs = qs.filter(
                Q(first_name__icontains=self.q) |
                Q(middle_name__icontains=self.q) |
                Q(last_name__icontains=self.q)
            )
        return qs.distinct()


# class FacultyAutocompleteView(autocomplete.Select2QuerySetView):

#     def get_queryset(self):
#         qs = EntityVersion.objects.all()
#         return qs.distinct()

class EntityAutocompleteView(autocomplete.Select2QuerySetView):

    def get_queryset(self):
        qs = Entity.objects.prefetch_related('entityversion_set').all()
        if self.q:
            qs = qs.filter(
                entityversion__acronym__icontains=self.q
            )
        return qs.distinct()


class PartnershipAutocompleteView(autocomplete.Select2QuerySetView):

    def get_queryset(self):
        qs = Partnership.objects.all()
        if self.q:
            qs = qs.filter(
                Q(partner__name__icontains=self.q)
                | Q(partner_entity__name__icontains=self.q)
            )
        return qs.distinct()


class PartnerAutocompleteView(autocomplete.Select2QuerySetView):

    def get_queryset(self):
        qs = Partner.objects.all()
        pk = self.forwarded.get('partner_pk', None)
        if self.q:
            qs = qs.filter(name__icontains=self.q)
        qs = qs.distinct()
        if pk is not None:
            print(pk)
            current = Partner.objects.get(pk=pk)
            return [current] + list(filter(lambda x: x.is_actif, qs))
        return list(filter(lambda x: x.is_actif, qs))


class PartnerEntityAutocompleteView(autocomplete.Select2QuerySetView):

    def get_queryset(self):
        qs = PartnerEntity.objects.all()
        partner = self.forwarded.get('partner', None)
        if partner:
            qs = qs.filter(partner=partner)
        else:
            return PartnerEntity.objects.none()
        if self.q:
            qs = qs.filter(name__icontain=self.q)
        return qs.distinct()


class UclUniversityAutocompleteView(autocomplete.Select2QuerySetView):

    def get_ucl_universities(self):
        qs = Entity.objects.filter(entityversion__entity_type=FACULTY)
        if not user_is_adri(self.request.user):
            qs = qs.filter(entitymanager__person__user=self.request.user)
        if self.q:
            qs = qs.filter(entityversion__acronym__icontains=self.q)
        return qs.distinct()

    def get_queryset(self):
        return sorted(self.get_ucl_universities(), key=lambda x: x.most_recent_acronym)

    def get_result_label(self, result):
        if result.entityversion_set:
            title = result.entityversion_set.latest("start_date").title
        else:
            return result.most_recent_acronym
        return '{0.most_recent_acronym} - {1}'.format(result, title)


class UclUniversityLaboAutocompleteView(autocomplete.Select2QuerySetView):

    def get_ucl_university_labos(self):
        qs = Entity.objects.all()
        ucl_university = self.forwarded.get('ucl_university', None)
        if ucl_university:
            qs = qs.filter(entityversion__parent=ucl_university)
        else:
            return Entity.objects.none()
        if self.q:
            qs = qs.filter(entityversion__acronym__icontains=self.q)
        return qs.distinct()

    def get_queryset(self):
        return sorted(
            self.get_ucl_university_labos(),
            key=lambda x: x.most_recent_acronym,
        )

    def get_result_label(self, result):
        title = result.entityversion_set.latest("start_date").title
        return '{0.most_recent_acronym} - {1}'.format(result, title)


class PartnershipYearEntitiesAutocompleteView(autocomplete.Select2QuerySetView):

    def get_queryset(self):
        qs = Entity.objects.all()
        if self.q:
            qs = qs.filter(title__icontains=self.q)
        return qs.distinct()

    def get_result_label(self, result):
        try:
            title = result.entityversion_set.latest("start_date").title
            return '{0.most_recent_acronym} - {1}'.format(result, title)
        except EntityVersion.DoesNotExist:
            return result.most_recent_acronym


class PartnershipYearOffersAutocompleteView(autocomplete.Select2QuerySetView):

    def get_queryset(self):
        qs = EducationGroupYear.objects.all().select_related('academic_year')
        if self.q:
            qs = qs.filter(title__icontains=self.q)
        return qs.distinct()

    def get_result_label(self, result):
        return '{0.acronym} - {0.title}'.format(result)


class UniversityOffersAutocompleteView(autocomplete.Select2QuerySetView):

    def get_queryset(self):
        qs = EducationGroupYear.objects.all().select_related('academic_year')
        ucl_university_labo = self.forwarded.get('ucl_university_labo', None)
        if ucl_university_labo:
            qs = qs.filter(Q(management_entity=ucl_university_labo) | Q(administration_entity=ucl_university_labo))
        else:
            return EducationGroupYear.objects.none()
        if self.q:
            qs = qs.filter(title__icontains=self.q)
        return qs.distinct()

    def get_result_label(self, result):
        return '{0.acronym} - {0.title}'.format(result)


# Partnership filters autocompletes

class PartnerAutocompletePartnershipsFilterView(autocomplete.Select2QuerySetView):

    def get_queryset(self):
        qs = Partner.objects.filter(partnerships__isnull=False)
        if self.q:
            qs = qs.filter(name__icontains=self.q)
        return qs.distinct()


class PartnerEntityAutocompletePartnershipsFilterView(autocomplete.Select2QuerySetView):

    def get_queryset(self):
        qs = PartnerEntity.objects.filter(partnerships__isnull=False)
        partner = self.forwarded.get('partner', None)
        if partner:
            qs = qs.filter(partner=partner)
        else:
            return PartnerEntity.objects.none()
        if self.q:
            qs = qs.filter(name__icontain=self.q)
        return qs.distinct()


class UclUniversityAutocompleteFilterView(UclUniversityAutocompleteView):

    def get_queryset(self):
        qs = super().get_ucl_universities()
        return sorted(qs.filter(partnerships__isnull=False), key=lambda x: x.most_recent_acronym)


class UclUniversityLaboAutocompleteFilterView(UclUniversityLaboAutocompleteView):

    def get_queryset(self):
        qs = super().get_ucl_university_labos()
        ucl_university = self.forwarded.get('ucl_university', None)
        if ucl_university:
            qs = qs.filter(partnerships_labo__ucl_university=ucl_university)
        else:
            return Entity.objects.none()
        return qs.distinct()


class UniversityOffersAutocompleteFilterView(UniversityOffersAutocompleteView):

    def get_queryset(self):
        qs = super().get_queryset()
        ucl_university_labo = self.forwarded.get('ucl_university_labo', None)
        if ucl_university_labo:
            qs = qs.filter(partnerships__ucl_university_labo=ucl_university_labo)
        else:
            return EducationGroupYear.objects.none()
        return qs.filter(partnerships__isnull=False).distinct()
