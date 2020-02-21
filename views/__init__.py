import codecs
import csv
import os
from copy import copy
from datetime import date

from dal import autocomplete
from django.conf import settings
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin, PermissionRequiredMixin
from django.contrib.postgres.aggregates import StringAgg
from django.core.exceptions import ValidationError
from django.core.mail import send_mail
from django.core.validators import URLValidator
from django.db import transaction
from django.db.models import (
    Exists, Max, OuterRef, Prefetch, Q, Subquery
)
from django.http import (
    FileResponse, Http404, HttpResponse,
    HttpResponseRedirect
)
from django.shortcuts import get_object_or_404, redirect
from django.template.loader import render_to_string
from django.urls import reverse, reverse_lazy
from django.utils.functional import cached_property
from django.utils.timezone import now
from django.utils.translation import gettext
from django.utils.translation import gettext_lazy as _
from django.views import View
from django.views.generic import DetailView, ListView
from django.views.generic.base import TemplateResponseMixin
from django.views.generic.detail import SingleObjectMixin
from django.views.generic.edit import (
    CreateView, DeleteView, FormMixin,
    ProcessFormView, UpdateView
)
from django.views.generic.list import MultipleObjectMixin

from base.models.academic_year import (
    AcademicYear, current_academic_year,
    find_academic_years
)
from base.models.education_group_year import EducationGroupYear
from base.models.entity import Entity
from base.models.entity_version import EntityVersion
from base.models.enums.entity_type import FACULTY
from base.models.person import Person
from partnership.forms import (
    ContactForm, FinancingFilterForm,
    FinancingImportForm, MediaForm, PartnershipAgreementForm,
    PartnershipConfigurationForm,
    PartnershipFilterForm, PartnershipForm,
    PartnershipYearForm, UCLManagementEntityForm
)
from partnership.models import (
    Financing, Partner, PartnerEntity, Partnership,
    PartnershipAgreement, PartnershipConfiguration,
    PartnershipYear, UCLManagementEntity, Media
)
from partnership.utils import academic_years, user_is_adri, user_is_gf
from reference.models.country import Country

from .export import ExportView
from .partner import *


class SimilarPartnerView(ListView, PermissionRequiredMixin):
    template_name = 'partnerships/partners/includes/similar_partners_preview.html'
    context_object_name = 'similar_partners'
    login_url = 'access_denied'
    permission_required = 'partnership.can_access_partnerships'

    def get_queryset(self):
        search = self.request.GET.get('search', '')
        # Don't query for small searches
        if len(search) < 3:
            return Partner.objects.none()
        return Partner.objects.filter(name__icontains=search)[:10]


class PartnerMediaMixin(UserPassesTestMixin):
    login_url = 'access_denied'

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
    login_url = 'access_denied'

    def get_template_names(self):
        if self.request.is_ajax():
            return 'partnerships/includes/media_form.html'
        return self.template_name

    def get_filename(self, filename):
        extension = filename.split('.')[-1]
        return 'partner_media_{}.{}'.format(self.partner.pk, extension)

    @transaction.atomic
    def form_valid(self, form):
        media = form.save(commit=False)
        if media.pk is None:
            media.author = self.request.user
        if media.file and not hasattr(form.cleaned_data['file'], 'path'):
            media.file.name = self.get_filename(media.file.name)
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
    login_url = 'access_denied'


class PartnerMediaUpdateView(LoginRequiredMixin, PartnerMediaFormMixin, UpdateView):
    template_name = 'partnerships/partners/medias/partner_media_update.html'
    context_object_name = 'media'
    login_url = 'access_denied'


class PartnerMediaDeleteView(LoginRequiredMixin, PartnerMediaMixin, DeleteView):
    template_name = 'partnerships/partners/medias/partner_media_delete.html'
    login_url = 'access_denied'

    def get_template_names(self):
        if self.request.is_ajax():
            return 'partnerships/includes/media_delete.html'
        return self.template_name


class PartnerMediaDownloadView(PartnerMediaMixin, SingleObjectMixin, View):
    login_url = 'access_denied'

    def get(self, request, *args, **kwargs):
        media = self.get_object()
        if media.file is None:
            raise Http404
        response = FileResponse(media.file)
        response['Content-Disposition'] = 'attachment; filename={}'.format(os.path.basename(media.file.name))
        return response


class PartnershipContactMixin(LoginRequiredMixin, UserPassesTestMixin):
    login_url = 'access_denied'

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
    login_url = 'access_denied'
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
    login_url = 'access_denied'

    def form_valid(self, form):
        contact = form.save()
        self.partnership.contacts.add(contact)
        messages.success(self.request, _("contact_creation_success"))
        return redirect(self.partnership)


class PartnershipContactUpdateView(PartnershipContactFormMixin, UpdateView):
    template_name = 'partnerships/contacts/partnership_contact_update.html'
    login_url = 'access_denied'

    def form_valid(self, form):
        form.save()
        messages.success(self.request, _("contact_update_success"))
        return redirect(self.partnership)


class PartnershipContactDeleteView(PartnershipContactMixin, DeleteView):
    template_name = 'partnerships/contacts/contact_confirm_delete.html'
    login_url = 'access_denied'

    def get_template_names(self):
        if self.request.is_ajax():
            return 'partnerships/contacts/includes/contact_delete_form.html'
        return self.template_name

    def delete(self, request, *args, **kwargs):
        response = super().delete(request, *args, **kwargs)
        messages.success(request, _("contact_delete_success"))
        return response


class PartnershipListFilterMixin(FormMixin, MultipleObjectMixin):
    form_class = PartnershipFilterForm
    login_url = 'access_denied'

    def get(self, *args, **kwargs):
        if not self.request.GET and user_is_gf(self.request.user):
            university = self.request.user.person.partnershipentitymanager_set.first().entity
            if Partnership.objects.filter(ucl_university=university).exists():
                return HttpResponseRedirect(
                    '?ucl_university={0}'
                        .format(self.request.user.person.partnershipentitymanager_set.first().entity.pk)
                )
        return super(PartnershipListFilterMixin, self).get(*args, **kwargs)

    def get_context_object_name(self, object_list):
        if self.is_agreements:
            return 'agreements'
        return 'partnerships'

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

    def get_form(self):
        try:
            return self.form
        except AttributeError:
            self.form = super().get_form()
            return self.form

    def get_ordering(self):
        ordering = self.request.GET.get('ordering', 'country')
        if self.is_agreements:
            if ordering == 'partner':
                return ['partnership__partner__name']
            elif ordering == '-partner':
                return ['-partnership__partner__name']
            if ordering == 'country':
                return [
                    'partnership__partner__contact_address__country__name',
                    'partnership__partner__contact_address__city',
                    'partnership__partner__name',
                ]
            elif ordering == '-country':
                return [
                    '-partnership__partner__contact_address__country__name',
                    '-partnership__partner__contact_address__city',
                    '-partnership__partner__name'
                ]
            elif ordering == 'ucl':
                return [
                    'partnership_ucl_university_parent_most_recent_acronym',
                    'partnership_ucl_university_most_recent_acronym',
                    'partnership_ucl_university_labo_most_recent_acronym',
                ]
            elif ordering == '-ucl':
                return [
                    '-partnership_ucl_university_parent_most_recent_acronym',
                    '-partnership_ucl_university_most_recent_acronym',
                    '-partnership_ucl_university_labo_most_recent_acronym',
                ]
            return [ordering]
        else:
            if ordering == 'country':
                return ['partner__contact_address__country__name', 'partner__contact_address__city', 'partner__name']
            elif ordering == '-country':
                return ['-partner__contact_address__country__name', '-partner__contact_address__city', '-partner__name']
            elif ordering == 'ucl':
                return [
                    'ucl_university_parent_most_recent_acronym',
                    'ucl_university_most_recent_acronym',
                    'ucl_university_labo_most_recent_acronym',
                ]
            elif ordering == '-ucl':
                return [
                    '-ucl_university_parent_most_recent_acronym',
                    '-ucl_university_most_recent_acronym',
                    '-ucl_university_labo_most_recent_acronym',
                ]
            else:
                return [ordering]

    def filter_queryset(self, queryset, data):
        if data.get('ucl_university', None):
            queryset = queryset.filter(ucl_university=data['ucl_university'])
        if data.get('ucl_university_labo', None):
            queryset = queryset.filter(ucl_university_labo=data['ucl_university_labo'])
        if data.get('education_level', None):
            queryset = queryset.filter(years__education_levels=data['education_level'])
        if data.get('years_entity', None):
            queryset = queryset.filter(Q(years__entities=data['years_entity']) | Q(years__entities__isnull=True))
        if data.get('university_offer', None):
            queryset = queryset.filter(Q(years__offers=data['university_offer']) | Q(years__offers__isnull=True))
        if data.get('partner', None):
            queryset = queryset.filter(partner=data['partner'])
        if data.get('partner_entity', None):
            queryset = queryset.filter(partner_entity=data['partner_entity'])
        if data.get('use_egracons', None) is not None:
            queryset = queryset.filter(partner__use_egracons=data['use_egracons'])
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
            queryset = (
                queryset
                .annotate(has_supervisor_with_entity=Exists(UCLManagementEntity.objects
                    .filter(
                        entity__isnull=False,
                        entity=OuterRef('ucl_university_labo'),
                        faculty=OuterRef('ucl_university'),
                        academic_responsible=data['supervisor'],
                    )
                ), has_supervisor_without_entity=Exists(UCLManagementEntity.objects
                    .filter(
                        entity__isnull=True,
                        faculty=OuterRef('ucl_university'),
                        academic_responsible=data['supervisor'],
                    )
                ))
                .filter(Q(supervisor=data['supervisor'])
                        | Q(supervisor__isnull=True,
                            has_supervisor_with_entity=True)
                        | Q(supervisor__isnull=True,
                            ucl_university_labo__isnull=True,
                            has_supervisor_without_entity=True))
            )
        if data.get('education_field', None):
            queryset = queryset.filter(years__education_fields=data['education_field'])
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
                        partnership=OuterRef('pk'),
                    ).filter(
                        start_academic_year__start_date__lte=partnership_not_valid_in.start_date,
                        end_academic_year__end_date__gte=partnership_not_valid_in.end_date,
                    ),
                ),
                not_valid_in_has_valid_agreements=Exists(
                    PartnershipAgreement.objects.filter(
                        partnership=OuterRef('pk'),
                    ).filter(
                        status=PartnershipAgreement.STATUS_VALIDATED,
                        start_academic_year__start_date__lte=partnership_not_valid_in.start_date,
                        end_academic_year__end_date__gte=partnership_not_valid_in.end_date,
                    ),
                )
            ).filter(not_valid_in_has_agreements=True, not_valid_in_has_valid_agreements=False)
        if data.get('partnership_with_no_agreements_in', None):
            partnership_with_no_agreements_in = data['partnership_with_no_agreements_in']
            # We need to use subqueries to avoid conflicts with other filters
            queryset = queryset.annotate(
                no_agreements_in_has_years=Exists(
                    PartnershipYear.objects.filter(
                        partnership=OuterRef('pk'),
                        academic_year=partnership_with_no_agreements_in,
                    )
                ),
                no_agreements_in_has_agreements=Exists(
                    PartnershipAgreement.objects.filter(
                        partnership=OuterRef('pk'),
                        start_academic_year__start_date__lte=partnership_with_no_agreements_in.start_date,
                        end_academic_year__end_date__gte=partnership_with_no_agreements_in.end_date,
                    )
                ),
            ).filter(no_agreements_in_has_years=True, no_agreements_in_has_agreements=False)
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
            .annotate(
                validity_end_year=Subquery(
                    AcademicYear.objects
                        .filter(
                            partnership_agreements_end__partnership=OuterRef('pk'),
                            partnership_agreements_end__status=PartnershipAgreement.STATUS_VALIDATED
                        )
                        .order_by('-end_date')
                        .values('year')[:1]
                ),
                ucl_university_parent_most_recent_acronym=Subquery(
                    EntityVersion.objects
                        .filter(entity__parent_of__entity=OuterRef('ucl_university__pk'))
                        .order_by('-start_date')
                        .values('acronym')[:1]
                ),
                ucl_university_parent_most_recent_title=Subquery(
                    EntityVersion.objects
                        .filter(entity__parent_of__entity=OuterRef('ucl_university__pk'))
                        .order_by('-start_date')
                        .values('title')[:1]
                ),
                ucl_university_most_recent_acronym=Subquery(
                    EntityVersion.objects
                        .filter(entity=OuterRef('ucl_university__pk'))
                        .order_by('-start_date')
                        .values('acronym')[:1]
                ),
                ucl_university_most_recent_title=Subquery(
                    EntityVersion.objects
                        .filter(entity=OuterRef('ucl_university__pk'))
                        .order_by('-start_date')
                        .values('title')[:1]
                ),
                ucl_university_labo_most_recent_acronym=Subquery(
                    EntityVersion.objects
                        .filter(entity=OuterRef('ucl_university_labo__pk'))
                        .order_by('-start_date')
                        .values('acronym')[:1]
                ),
                ucl_university_labo_most_recent_title=Subquery(
                    EntityVersion.objects
                        .filter(entity=OuterRef('ucl_university_labo__pk'))
                        .order_by('-start_date')
                        .values('title')[:1]
                ),
            )
        )
        form = self.get_form()
        if not form.is_bound:
            queryset = self.filter_queryset(queryset, self.get_initial())
        elif form.is_valid():
            queryset = self.filter_queryset(queryset, form.cleaned_data)
        ordering = self.get_ordering()
        if self.is_agreements:
            queryset = self.get_agreements_queryset(queryset).order_by(*ordering)
        else:
            queryset = queryset.order_by(*ordering)
        return queryset.distinct()

    def get_agreements_queryset(self, partnerships):
        return (
            PartnershipAgreement.objects
            .annotate(
                # Used for ordering
                partnership_ucl_university_parent_most_recent_acronym=Subquery(
                    EntityVersion.objects
                        .filter(entity__parent_of__entity=OuterRef('partnership__ucl_university__pk'))
                        .order_by('-start_date')
                        .values('acronym')[:1]
                ),
                partnership_ucl_university_most_recent_acronym=Subquery(
                    EntityVersion.objects
                        .filter(entity=OuterRef('partnership__ucl_university__pk'))
                        .order_by('-start_date')
                        .values('acronym')[:1]
                ),
                partnership_ucl_university_labo_most_recent_acronym=Subquery(
                    EntityVersion.objects
                        .filter(entity=OuterRef('partnership__ucl_university_labo__pk'))
                        .order_by('-start_date')
                        .values('acronym')[:1]
                ),
            ).filter(
                partnership__in=partnerships
            ).select_related(
                'partnership__partner__contact_address__country',
                'partnership__supervisor',
                'partnership__ucl_university',
                'partnership__ucl_university_labo',
                'start_academic_year',
                'end_academic_year',
            )
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['is_agreements'] = self.is_agreements
        context['can_search_agreements'] = user_is_adri(self.request.user)
        return context

    @cached_property
    def is_agreements(self):
        if not user_is_adri(self.request.user):
            return False
        if self.request.method == "GET":
            if "search_partnership" in self.request.GET:
                return False
            if "search_agreement" in self.request.GET:
                return True
            return self.request.GET.get('agreements', False)
        return False


class PartnershipsListView(PermissionRequiredMixin, PartnershipListFilterMixin, ListView):
    template_name = 'partnerships/partnerships_list.html'
    context_object_name = 'partnerships'
    paginate_by = 20
    paginate_orphans = 2
    paginate_neighbours = 4
    login_url = 'access_denied'
    permission_required = 'partnership.can_access_partnerships'

    def get_template_names(self):
        if self.is_agreements:
            if self.request.is_ajax():
                return 'partnerships/agreements/includes/agreements_list_results.html'
            else:
                return 'partnerships/partnerships_list.html'
        else:
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


class PartnershipAgreementExportView(PermissionRequiredMixin, PartnershipListFilterMixin, ExportView):
    login_url = 'access_denied'
    permission_required = 'partnership.can_access_partnerships'

    @cached_property
    def is_agreements(self):
        return True

    def get_xls_headers(self):
        return [
            gettext('id'),
            gettext('partner'),
            gettext('country'),
            gettext('city'),
            gettext('partnership_supervisor'),
            gettext('faculty'),
            gettext('entity'),
            gettext('academic_years'),
            gettext('start_academic_year'),
            gettext('end_academic_year'),
            gettext('status'),
        ]

    def get_xls_data(self):
        queryset = self.get_queryset().prefetch_related(
            Prefetch(
                'partnership__ucl_university__entityversion_set',
                queryset=EntityVersion.objects.order_by('start_date'),
                to_attr='faculties',
            ),
        )
        for agreement in queryset:
            faculty = agreement.partnership.ucl_university.faculties[0]
            entity = agreement.partnership.ucl_university_labo
            years = academic_years(agreement.start_academic_year, agreement.end_academic_year)
            yield [
                agreement.pk,
                str(agreement.partnership.partner),
                str(agreement.partnership.partner.contact_address.country),
                str(agreement.partnership.partner.contact_address.city),
                str(agreement.partnership.supervisor),
                faculty.acronym,
                entity.most_recent_acronym if entity is not None else '',
                years,
                agreement.start_academic_year.year,
                agreement.end_academic_year.year + 1,
                agreement.get_status_display(),
            ]

    def get_description(self):
        return _('agreements')

    def get_filename(self):
        return now().strftime('agreements-%Y-%m-%d-%H-%M-%S')

    def get_title(self):
        return _('agreements')


class PartnershipExportView(PermissionRequiredMixin, PartnershipListFilterMixin, ExportView):
    login_url = 'access_denied'
    permission_required = 'partnership.can_access_partnerships'

    @cached_property
    def is_agreements(self):
        return False

    def get_xls_headers(self):
        return [
            gettext('id'),
            gettext('partner'),
            gettext('partner_code'),
            gettext('erasmus_code'),
            gettext('pic_code'),
            gettext('partner_entity'),
            gettext('ucl_university'),
            gettext('ucl_university_labo'),
            gettext('supervisor'),
            gettext('partnership_year_entities'),
            gettext('partnership_year_education_levels'),
            gettext('tags'),
            gettext('created'),
            gettext('modified'),
            gettext('author'),
            gettext('is_sms'),
            gettext('is_smp'),
            gettext('is_sta'),
            gettext('is_stt'),
            gettext('start_academic_year'),
            gettext('end_academic_year'),
            gettext('is_valid'),
            gettext('external_id'),
            gettext('eligible'),
        ]

    def get_xls_data(self):
        queryset = self.get_queryset()
        queryset = (
            queryset
            .annotate(
                tags_list=StringAgg('tags__value', ', '),
                is_valid=Exists(
                    PartnershipAgreement.objects
                        .filter(status=PartnershipAgreement.STATUS_VALIDATED,
                                partnership=OuterRef('pk'))
                ),
            )
            .prefetch_related(
                Prefetch(
                    'years',
                    queryset=PartnershipYear.objects
                        .select_related('academic_year')
                        .prefetch_related(
                            Prefetch(
                                'entities',
                                queryset=Entity.objects.annotate(
                                    most_recent_acronym=Subquery(
                                        EntityVersion.objects
                                            .filter(entity=OuterRef('pk'))
                                            .order_by('-start_date')
                                            .values('acronym')[:1]
                                    ),
                                )
                            ),
                            'education_levels',
                        )
                ),
            )
            .select_related('author')
        )
        for partnership in queryset.distinct():

            first_year = None
            current_year = None
            end_year = None
            years = partnership.years.all()
            if years:
                first_year = years[0]
            for year in years:
                end_year = year
                if year.academic_year == self.academic_year:
                    current_year = year

            yield [
                partnership.pk,
                str(partnership.partner),
                str(partnership.partner.partner_code) if partnership.partner.partner_code is not None else '',
                str(partnership.partner.erasmus_code) if partnership.partner.erasmus_code is not None else '',
                str(partnership.partner.pic_code) if partnership.partner.pic_code is not None else '',
                str(partnership.partner_entity) if partnership.partner_entity else None,
                str(partnership.ucl_university_most_recent_acronym),
                str(partnership.ucl_university_labo_most_recent_acronym)
                    if partnership.ucl_university_labo_most_recent_acronym is not None else '',
                str(partnership.supervisor) if partnership.supervisor is not None else '',
                ', '.join(map(lambda x: x.most_recent_acronym, current_year.entities.all()))
                    if current_year is not None else '',
                ', '.join(map(str, current_year.education_levels.all())) if current_year is not None else '',
                partnership.tags_list,
                partnership.created.strftime('%Y-%m-%d'),
                partnership.modified.strftime('%Y-%m-%d'),
                str(partnership.author),
                current_year.is_sms if current_year is not None else '',
                current_year.is_smp if current_year is not None else '',
                current_year.is_sta if current_year is not None else '',
                current_year.is_stt if current_year is not None else '',
                first_year.academic_year if first_year is not None else '',
                end_year.academic_year if end_year is not None else '',
                partnership.is_valid,
                partnership.external_id,
                current_year.eligible if current_year is not None else '',
            ]

    def get_description(self):
        return _('partnerships')

    def get_filename(self):
        return now().strftime('partnerships-%Y-%m-%d-%H-%M-%S')

    def get_title(self):
        return _('partnerships')

    def get_xls_filters(self):
        filters = super(PartnershipExportView, self).get_xls_filters()
        filters[_('academic_year')] = str(self.academic_year)
        filters.move_to_end(_('academic_year'), last=False)
        return filters

    def get(self, *args, **kwargs):
        configuration = PartnershipConfiguration.get_configuration()
        self.academic_year = configuration.get_current_academic_year_for_creation_modification()
        return super(PartnershipExportView, self).get(*args, **kwargs)


class PartnershipDetailView(PermissionRequiredMixin, DetailView):
    model = Partnership
    context_object_name = 'partnership'
    template_name = 'partnerships/partnership_detail.html'
    login_url = 'access_denied'
    permission_required = 'partnership.can_access_partnerships'

    def get_context_data(self, **kwargs):
        context = super(PartnershipDetailView, self).get_context_data(**kwargs)
        context['can_change'] = self.object.user_can_change(self.request.user)
        if self.object.current_year is None:
            context['show_more_year_link'] = self.object.years.count() > 1
        else:
            year = self.object.current_year.academic_year.year
            context['show_more_year_link'] = \
                self.object.years.exclude(academic_year__year__in=[year, year + 1]).exists()
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
                    'medias',
                    queryset=Media.objects.select_related('type'),
                ),
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
    login_url = 'access_denied'

    def get_form_year(self):
        kwargs = self.get_form_kwargs()
        kwargs['prefix'] = 'year'
        partnership = kwargs['instance']
        if partnership is not None:
            configuration = PartnershipConfiguration.get_configuration()
            current_academic_year = configuration.get_current_academic_year_for_creation_modification()
            kwargs['instance'] = partnership.years.filter(academic_year=current_academic_year).first()
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
    login_url = 'access_denied'

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
        if not user_is_adri(self.request.user):
            send_mail(
                'OSIS-Partenariats : {} - {}'.format(
                    _('partnership_created'), partnership.ucl_university.most_recent_acronym),
                render_to_string(
                    'partnerships/mails/plain_partnership_creation.html',
                    context={
                        'user': self.request.user,
                        'partnership': partnership,
                    },
                    request=self.request,
                ),
                settings.DEFAULT_FROM_EMAIL,
                [PartnershipConfiguration.get_configuration().email_notification_to],
                html_message=render_to_string(
                    'partnerships/mails/partnership_creation.html',
                    context={
                        'user': self.request.user,
                        'partnership': partnership,
                    },
                    request=self.request,
                ),
            )
        return redirect(partnership)

    def post(self, request, *args, **kwargs):
        self.object = None
        return super(PartnershipCreateView, self).post(request, *args, **kwargs)


class PartnershipUpdateView(LoginRequiredMixin, UserPassesTestMixin, PartnershipFormMixin, UpdateView):
    model = Partnership
    form_class = PartnershipForm
    template_name = "partnerships/partnership_update.html"
    login_url = 'access_denied'

    def dispatch(self, *args, **kwargs):
        self.object = self.get_object()
        return super().dispatch(*args, **kwargs)

    def test_func(self):
        return self.get_object().user_can_change(self.request.user)

    @transaction.atomic
    def form_valid(self, form, form_year):
        partnership = form.save()

        if (form_year.cleaned_data['end_academic_year'] != self.object.end_academic_year
                and not user_is_adri(self.request.user)):
            send_mail(
                'OSIS-Partenariats : {}'.format(
                    _('partnership_end_year_updated_{partner}_{faculty}').format(
                        partner=partnership.partner, faculty=partnership.ucl_university.most_recent_acronym
                    )
                ),
                render_to_string(
                    'partnerships/mails/plain_partnership_update.html',
                    context={
                        'user': self.request.user,
                        'partnership': partnership,
                    },
                    request=self.request,
                ),
                settings.DEFAULT_FROM_EMAIL,
                [PartnershipConfiguration.get_configuration().email_notification_to],
                html_message=render_to_string(
                    'partnerships/mails/partnership_update.html',
                    context={
                        'user': self.request.user,
                        'partnership': partnership,
                    },
                    request=self.request,
                ),
            )

        start_academic_year = form_year.cleaned_data.get('start_academic_year', None)
        from_year = form_year.cleaned_data.get('from_academic_year', None)
        end_year = form_year.cleaned_data.get('end_academic_year', None).year
        if from_year is None:
            from_year = start_academic_year.year
        else:
            from_year = from_year.year

        # Create missing start year if needed
        if start_academic_year is not None:
            start_year = start_academic_year.year
            first_year = partnership.years.order_by('academic_year__year').select_related('academic_year').first()
            if first_year is not None:
                first_year_education_fields = first_year.education_fields.all()
                first_year_education_levels = first_year.education_levels.all()
                first_year_entities = first_year.entities.all()
                first_year_offers = first_year.offers.all()
                academic_years = find_academic_years(start_year=start_year, end_year=first_year.academic_year.year - 1)
                for academic_year in academic_years:
                    first_year.id = None
                    first_year.academic_year = academic_year
                    first_year.save()
                    first_year.education_fields.set(first_year_education_fields)
                    first_year.education_levels.set(first_year_education_levels)
                    first_year.entities.set(first_year_entities)
                    first_year.offers.set(first_year_offers)

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
                partnership_year.partnership = partnership
            partnership_year.academic_year = academic_year
            partnership_year.save()
            form_year.save_m2m()

        # Delete no longer used years
        query = Q(academic_year__year__gt=end_year)
        if start_academic_year is not None:
            query |= Q(academic_year__year__lt=start_year)
        PartnershipYear.objects.filter(partnership=partnership).filter(query).delete()

        messages.success(self.request, _('partnership_success'))
        return redirect(partnership)


class PartnershipMediaMixin(UserPassesTestMixin):
    login_url = 'access_denied'

    def dispatch(self, request, *args, **kwargs):
        self.partnership = get_object_or_404(Partnership, pk=kwargs['partnership_pk'])
        return super(PartnershipMediaMixin, self).dispatch(request, *args, **kwargs)

    def test_func(self):
        return self.partnership.user_can_change(self.request.user)

    def get_queryset(self):
        return self.partnership.medias.all()

    def get_success_url(self):
        return self.partnership.get_absolute_url()

    def get_context_data(self, **kwargs):
        context = super(PartnershipMediaMixin, self).get_context_data(**kwargs)
        context['partnership'] = self.partnership
        return context


class PartnershipMediaFormMixin(PartnershipMediaMixin, FormMixin):
    form_class = MediaForm
    login_url = 'access_denied'

    def get_template_names(self):
        if self.request.is_ajax():
            return 'partnerships/includes/media_form.html'
        return self.template_name

    def get_filename(self, filename):
        extension = filename.split('.')[-1]
        return 'partnership_media_{}.{}'.format(self.partnership.pk, extension)

    @transaction.atomic
    def form_valid(self, form):
        media = form.save(commit=False)
        if media.pk is None:
            media.author = self.request.user
        if media.file and not hasattr(form.cleaned_data['file'], 'path'):
            media.file.name = self.get_filename(media.file.name)
        media.save()
        form.save_m2m()
        self.partnership.medias.add(media)
        messages.success(self.request, _('partnership_media_saved'))
        return redirect(self.partnership)

    def form_invalid(self, form):
        messages.error(self.request, _('partnership_media_error'))
        return super(PartnershipMediaFormMixin, self).form_invalid(form)


class PartnershipMediaCreateView(LoginRequiredMixin, PartnershipMediaFormMixin, CreateView):
    template_name = 'partnerships/medias/partnership_media_create.html'
    login_url = 'access_denied'


class PartnershipMediaUpdateView(LoginRequiredMixin, PartnershipMediaFormMixin, UpdateView):
    template_name = 'partnerships/medias/partnership_media_update.html'
    context_object_name = 'media'
    login_url = 'access_denied'


class PartnershipMediaDeleteView(LoginRequiredMixin, PartnershipMediaMixin, DeleteView):
    template_name = 'partnerships/medias/partnership_media_delete.html'
    login_url = 'access_denied'

    def get_template_names(self):
        if self.request.is_ajax():
            return 'partnerships/includes/media_delete.html'
        return self.template_name


class PartnershipMediaDownloadView(PartnershipMediaMixin, SingleObjectMixin, View):
    login_url = 'access_denied'

    def get(self, request, *args, **kwargs):
        media = self.get_object()
        if media.file is None:
            raise Http404
        response = FileResponse(media.file)
        response['Content-Disposition'] = 'attachment; filename={}'.format(os.path.basename(media.file.name))
        return response


class PartnershipAgreementsMixin(LoginRequiredMixin, UserPassesTestMixin):
    context_object_name = 'agreement'
    login_url = 'access_denied'

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
    login_url = 'access_denied'

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
        form = MediaForm(**kwargs)
        del form.fields['type']
        return form

    def get_context_data(self, **kwargs):
        if 'form_media' not in kwargs:
            kwargs['form_media'] = self.get_form_media()
        return super(PartnershipAgreementsFormMixin, self).get_context_data(**kwargs)

    def check_dates(self, agreement):
        if agreement.start_academic_year.year < self.partnership.start_academic_year.year:
            messages.warning(self.request, _('partnership_agreement_warning_before'))
        if agreement.end_academic_year.year > self.partnership.end_academic_year.year:
            messages.warning(self.request, _('partnership_agreement_warning_after'))

    def get_filename(self, filename):
        extension = filename.split('.')[-1]
        return 'partnership_agreement_{}_{}.{}'.format(self.partnership.pk, self.partnership.partner.pk, extension)

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
    login_url = 'access_denied'

    def test_func(self):
        return self.partnership.user_can_change(self.request.user)

    @transaction.atomic
    def form_valid(self, form, form_media):
        media = form_media.save(commit=False)
        media.author = self.request.user
        if media.file:
            media.file.name = self.get_filename(media.file.name)
        media.save()
        form_media.save_m2m()
        agreement = form.save(commit=False)
        agreement.partnership = self.partnership
        agreement.media = media
        agreement.save()
        form.save_m2m()
        self.check_dates(agreement)
        messages.success(self.request, _('partnership_agreement_success'))
        return redirect(self.partnership)

    def post(self, request, *args, **kwargs):
        self.object = None
        return super(PartneshipAgreementCreateView, self).post(request, *args, **kwargs)


class PartneshipAgreementUpdateView(PartnershipAgreementsFormMixin, UpdateView):
    template_name = 'partnerships/agreements/update.html'
    login_url = 'access_denied'

    def test_func(self):
        return self.get_object().user_can_change(self.request.user)

    def get_queryset(self):
        return PartnershipAgreement.objects.select_related('start_academic_year', 'end_academic_year')

    @transaction.atomic
    def form_valid(self, form, form_media):
        media = form_media.save(commit=False)
        if media.file and not hasattr(form_media.cleaned_data['file'], 'path'):
            media.file.name = self.get_filename(media.file.name)
        media.save()
        form_media.save_m2m()
        agreement = form.save()
        self.check_dates(agreement)
        messages.success(self.request, _('partnership_agreement_success'))
        return redirect(self.partnership)

    def post(self, request, *args, **kwargs):
        self.object = self.get_object()
        return super(PartneshipAgreementUpdateView, self).post(request, *args, **kwargs)


class PartneshipAgreementDeleteView(PartnershipAgreementsMixin, DeleteView):
    template_name = 'partnerships/agreements/delete.html'
    login_url = 'access_denied'

    def test_func(self):
        return self.get_object().user_can_delete(self.request.user)

    def get_template_names(self):
        if self.request.is_ajax():
            return 'partnerships/agreements/includes/delete.html'
        return self.template_name


class PartnershipAgreementMediaDownloadView(PartnershipAgreementsMixin, SingleObjectMixin, View):
    login_url = 'access_denied'

    def test_func(self):
        return self.partnership.user_can_change(self.request.user)

    def get(self, request, *args, **kwargs):
        agreement = self.get_object()
        media = agreement.media
        if media.file is None:
            raise Http404
        response = FileResponse(media.file)
        response['Content-Disposition'] = 'attachment; filename={}'.format(os.path.basename(media.file.name))
        return response


class PartneshipConfigurationUpdateView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    form_class = PartnershipConfigurationForm
    template_name = 'partnerships/configuration_update.html'
    success_url = reverse_lazy('partnerships:list')
    login_url = 'access_denied'

    def test_func(self):
        return user_is_adri(self.request.user)

    def get_object(self, queryset=None):
        return PartnershipConfiguration.get_configuration()

    def form_valid(self, form):
        messages.success(self.request, _('configuration_saved'))
        return super().form_valid(form)


# UCLManagementEntities views :

class UCLManagementEntityListView(LoginRequiredMixin, UserPassesTestMixin, ListView):
    model = UCLManagementEntity
    template_name = "partnerships/ucl_management_entities/uclmanagemententity_list.html"
    context_object_name = "ucl_management_entities"
    login_url = 'access_denied'

    def test_func(self):
        result = UCLManagementEntity.user_can_list(self.request.user)
        return result

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['can_create_ucl_management_entity'] = UCLManagementEntity.user_can_create(self.request.user)
        return context

    def get_queryset(self):
        queryset = (
            UCLManagementEntity.objects
            .annotate(
                faculty_most_recent_acronym=Subquery(
                    EntityVersion.objects
                        .filter(entity=OuterRef('faculty__pk'))
                        .order_by('-start_date')
                        .values('acronym')[:1]
                ),
                entity_most_recent_acronym=Subquery(
                    EntityVersion.objects
                        .filter(entity=OuterRef('entity__pk'))
                        .order_by('-start_date')
                        .values('acronym')[:1]
                ),
            )
            .order_by('faculty_most_recent_acronym', 'entity_most_recent_acronym')
            .select_related('academic_responsible', 'administrative_responsible')
        )
        if not user_is_adri(self.request.user):
            queryset = queryset.filter(
                Q(faculty__partnershipentitymanager__person__user=self.request.user)
                | Q(faculty__entityversion__parent__partnershipentitymanager__person__user=self.request.user)
            )
        return queryset.distinct()


class UCLManagementEntityCreateView(LoginRequiredMixin, UserPassesTestMixin, CreateView):
    model = UCLManagementEntity
    template_name = "partnerships/ucl_management_entities/uclmanagemententity_create.html"
    form_class = UCLManagementEntityForm
    success_url = reverse_lazy('partnerships:ucl_management_entities:list')
    login_url = 'access_denied'

    def test_func(self):
        result = UCLManagementEntity.user_can_create(self.request.user)
        return result

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user
        return kwargs

    def form_valid(self, form):
        messages.success(self.request, _('ucl_management_entity_create_success'))
        return super().form_valid(form)


class UCLManagementEntityUpdateView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    model = UCLManagementEntity
    template_name = "partnerships/ucl_management_entities/uclmanagemententity_update.html"
    form_class = UCLManagementEntityForm
    context_object_name = "ucl_management_entity"
    success_url = reverse_lazy('partnerships:ucl_management_entities:list')
    login_url = 'access_denied'

    def test_func(self):
        self.object = self.get_object()
        result = self.object.user_can_change(self.request.user)
        return result

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user
        return kwargs

    def form_valid(self, form):
        messages.success(self.request, _('ucl_management_entity_change_success'))
        return super().form_valid(form)


class UCLManagementEntityDeleteView(LoginRequiredMixin, UserPassesTestMixin, DeleteView):
    model = UCLManagementEntity
    template_name = "partnerships/ucl_management_entities/uclmanagemententity_delete.html"
    context_object_name = "ucl_management_entity"
    success_url = reverse_lazy('partnerships:ucl_management_entities:list')
    login_url = 'access_denied'

    def get_template_names(self):
        if self.request.is_ajax():
            return 'partnerships/ucl_management_entities/includes/uclmanagemententity_delete_form.html'
        return self.template_name

    def test_func(self):
        return self.get_object().user_can_delete(self.request.user)


# Financing views :


class FinancingExportView(LoginRequiredMixin, UserPassesTestMixin, View):
    login_url = 'access_denied'

    def test_func(self):
        return user_is_adri(self.request.user)

    def get_csv_data(self, academic_year):
        countries = Country.objects.all().order_by('name').prefetch_related(
            Prefetch(
                'financing_set',
                queryset=Financing.objects.prefetch_related(
                    'academic_year'
                ).filter(academic_year=academic_year)
            )
        )
        for country in countries:
            if country.financing_set.all():
                for financing in country.financing_set.all():
                    row = {
                        'country': country.iso_code,
                        'name': financing.name,
                        'url': financing.url,
                        'country_name': country.name,
                    }
                    yield row
            else:
                row = {
                    'country': country.iso_code,
                    'name': '',
                    'url': '',
                    'country_name': country.name,
                }
                yield row

    def get(self, *args, year=None, **kwargs):
        if year is None:
            configuration = PartnershipConfiguration.get_configuration()
            self.academic_year = configuration.get_current_academic_year_for_creation_modification()
        else:
            self.academic_year = get_object_or_404(AcademicYear, year=year)

        filename = "financings_{}".format(self.academic_year)

        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename={}.csv'.format(filename)

        fieldnames = ['country_name', 'country', 'name', 'url']
        wr = csv.DictWriter(response, delimiter=';', quoting=csv.QUOTE_NONE, fieldnames=fieldnames)
        wr.writeheader()
        for row in self.get_csv_data(academic_year=self.academic_year):
            wr.writerow(row)
        return response


class FinancingImportView(LoginRequiredMixin, UserPassesTestMixin, TemplateResponseMixin, FormMixin, ProcessFormView):
    form_class = FinancingImportForm
    template_name = "partnerships/financings/financing_import.html"
    login_url = 'access_denied'

    def test_func(self):
        return user_is_adri(self.request.user)

    def get_success_url(self, academic_year=None):
        if academic_year is None:
            configuration = PartnershipConfiguration.get_configuration()
            academic_year = configuration.get_current_academic_year_for_creation_modification()
        return reverse('partnerships:financings:list', kwargs={'year': academic_year.year})

    def get_reader(self, csv_file):
        sample = csv_file.read(1024).decode('utf8')
        dialect = csv.Sniffer().sniff(sample)
        csv_file.seek(0)
        reader = csv.DictReader(
            codecs.iterdecode(csv_file, 'utf8'),
            fieldnames=['country_name', 'country', 'name', 'url'],
            dialect=dialect,
        )
        return reader

    def handle_csv(self, reader):
        url_validator = URLValidator()
        financings_countries = {}
        financings_url = {}
        next(reader, None)
        for row in reader:
            if not row['name']:
                continue
            try:
                country = Country.objects.get(iso_code=row['country'])
            except Country.DoesNotExist:
                messages.warning(
                    self.request, _('financing_country_not_imported_{country}').format(country=row['country']))
                continue
            if row['name'] not in financings_url:
                url = row['url']
                try:
                    if url:
                        url_validator(url)
                    financings_url[row['name']] = url
                except ValidationError:
                    financings_url[row['name']] = ''
                    messages.warning(
                        self.request, _('financing_url_invalid_{country}_{url}').format(country=country, url=url))
            financings_countries.setdefault(row['name'], []).append(country)
        return financings_countries, financings_url

    @transaction.atomic
    def update_financings(self, academic_year, financings_countries, financings_url):
        Financing.objects.filter(academic_year=academic_year).delete()
        financings = []
        for name in financings_countries.keys():
            financings.append(
                Financing(
                    academic_year=academic_year,
                    name=name,
                    url=financings_url.get(name, None)
                )
            )
        financings = Financing.objects.bulk_create(financings)
        for financing in financings:
            financing.countries.set(financings_countries.get(financing.name, []))

    def form_valid(self, form):
        academic_year = form.cleaned_data.get('import_academic_year')

        reader = self.get_reader(self.request.FILES['csv_file'])
        try:
            financings_countries, financings_url = self.handle_csv(reader)
        except ValueError:
            messages.error(self.request, _('financings_imported_error'))
            return redirect(self.get_success_url(academic_year))

        self.update_financings(academic_year, financings_countries, financings_url)

        messages.success(self.request, _('financings_imported'))
        return redirect(self.get_success_url(academic_year))


class FinancingListView(LoginRequiredMixin, UserPassesTestMixin, FormMixin, ListView):
    model = Country
    template_name = "partnerships/financings/financing_list.html"
    form_class = FinancingFilterForm
    context_object_name = "countries"
    paginate_by = 25
    paginate_orphans = 2
    paginate_neighbours = 3
    login_url = 'access_denied'

    def test_func(self):
        return user_is_adri(self.request.user)

    def dispatch(self, *args, year=None, **kwargs):
        if year is None:
            configuration = PartnershipConfiguration.get_configuration()
            self.academic_year = configuration.get_current_academic_year_for_creation_modification()
        else:
            self.academic_year = get_object_or_404(AcademicYear, year=year)

        if self.request.method == "POST":
            self.import_form = FinancingImportForm(self.request.POST, self.request.FILES)
            self.form = FinancingFilterForm(self.request.POST)
        else:
            self.import_form = FinancingImportForm(initial={'import_academic_year': self.academic_year})
            self.form = FinancingFilterForm(initial={'year': self.academic_year})
        return super().dispatch(*args, **kwargs)

    def get_ordering(self):
        ordering = self.request.GET.get('ordering', None)
        if ordering == 'financing_name':
            return [
                'financing_name',
                'name',
            ]
        elif ordering == '-financing_name':
            return [
                '-financing_name',
                'name',
            ]
        elif ordering == 'financing_url':
            return [
                'financing_url',
                'name',
            ]
        elif ordering == '-financing_url':
            return [
                '-financing_url',
                'name',
            ]
        elif ordering == '-name':
            return [
                '-name',
                'iso_code',
            ]
        else:
            return [
                'name',
                'iso_code'
            ]

    def post(self, *args, **kwargs):
        if self.form.is_valid():
            return self.form_valid(self.form)
        return self.form_invalid(self.form)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['import_form'] = self.import_form
        context['paginate_neighbours'] = self.paginate_neighbours
        context['can_import_financing'] = Financing.user_can_import(self.request.user)
        context['can_export_financing'] = Financing.user_can_export(self.request.user)
        context['academic_year'] = self.academic_year
        return context

    def get_success_url(self):
        return reverse('partnerships:financings:list', kwargs={'year': self.academic_year.year})

    def get_queryset(self):
        queryset = (
            Country.objects
            .annotate(
                financing_name=Subquery(
                    Financing.objects
                        .filter(countries=OuterRef('pk'), academic_year=self.academic_year)
                        .values('name')[:1]
                ),
                financing_url=Subquery(
                    Financing.objects
                        .filter(countries=OuterRef('pk'), academic_year=self.academic_year)
                        .values('url')[:1]
                ),
            )
            .order_by(*self.get_ordering())
            .distinct()
        )
        return queryset

    def form_valid(self, form):
        self.academic_year = form.cleaned_data.get('year', None)
        if self.academic_year is None:
            configuration = PartnershipConfiguration.get_configuration()
            self.academic_year = configuration.get_current_academic_year_for_creation_modification()
        return redirect(self.get_success_url())


# Autocompletes


class PersonAutocompleteView(PermissionRequiredMixin, autocomplete.Select2QuerySetView):
    login_url = 'access_denied'
    permission_required = 'partnership.can_access_partnerships'

    def get_queryset(self):
        qs = Person.objects.filter(employee=True)
        if self.q:
            qs = qs.filter(
                Q(first_name__icontains=self.q) |
                Q(middle_name__icontains=self.q) |
                Q(last_name__icontains=self.q)
            )
        return qs.distinct()

    def get_result_label(self, person):
        return '{0} - {1}'.format(person, person.email)


class EntityAutocompleteView(PermissionRequiredMixin, autocomplete.Select2QuerySetView):
    login_url = 'access_denied'
    permission_required = 'partnership.can_access_partnerships'

    def get_queryset(self):
        qs = Entity.objects.prefetch_related('entityversion_set').all()
        if self.q:
            qs = qs.filter(
                entityversion__acronym__icontains=self.q
            )
        return qs.distinct()


class PartnershipAutocompleteView(PermissionRequiredMixin, autocomplete.Select2QuerySetView):
    login_url = 'access_denied'
    permission_required = 'partnership.can_access_partnerships'

    def get_queryset(self):
        qs = Partnership.objects.all()
        if self.q:
            qs = qs.filter(
                Q(partner__name__icontains=self.q)
                | Q(partner_entity__name__icontains=self.q)
            )
        return qs.distinct()


class PartnerAutocompleteView(PermissionRequiredMixin, autocomplete.Select2QuerySetView):
    login_url = 'access_denied'
    permission_required = 'partnership.can_access_partnerships'

    def get_results(self, context):
        """Return data for the 'results' key of the response."""
        return [
            {
                'id': self.get_result_value(result),
                'text': self.get_result_label(result),
                'pic_code': result.pic_code,
                'erasmus_code': result.erasmus_code,
            } for result in context['object_list']
        ]

    def get_queryset(self):
        qs = Partner.objects.all()
        pk = self.forwarded.get('partner_pk', None)
        if self.q:
            qs = qs.filter(name__icontains=self.q)
        qs = qs.distinct()
        if pk is not None:
            current = Partner.objects.get(pk=pk)
            return [current] + list(filter(lambda x: x.is_actif, qs))
        return list(filter(lambda x: x.is_actif, qs))


class PartnerEntityAutocompleteView(PermissionRequiredMixin, autocomplete.Select2QuerySetView):
    login_url = 'access_denied'
    permission_required = 'partnership.can_access_partnerships'

    def get_queryset(self):
        qs = PartnerEntity.objects.all()
        partner = self.forwarded.get('partner', None)
        if partner:
            qs = qs.filter(partner=partner)
        else:
            return PartnerEntity.objects.none()
        if self.q:
            qs = qs.filter(name__icontains=self.q)
        return qs.distinct()


class FacultyAutocompleteView(PermissionRequiredMixin, autocomplete.Select2QuerySetView):
    login_url = 'access_denied'
    permission_required = 'partnership.can_access_partnerships'

    def get_queryset(self):
        qs = (
            Entity.objects
                .annotate(
                    most_recent_acronym=Subquery(
                        EntityVersion.objects
                            .filter(entity=OuterRef('pk'))
                            .order_by('-start_date')
                            .values('acronym')[:1]
                    ),
                )
                .filter(entityversion__entity_type=FACULTY)
        )
        if not user_is_adri(self.request.user):
            qs = qs.filter(
                Q(partnershipentitymanager__person__user=self.request.user)
                | Q(entityversion__parent__partnershipentitymanager__person__user=self.request.user)
            )
        if self.q:
            qs = qs.filter(most_recent_acronym__icontains=self.q)
        qs = qs.order_by('most_recent_acronym')
        return qs.distinct()

    def get_result_label(self, result):
        if result.entityversion_set:
            title = result.entityversion_set.latest("start_date").title
        else:
            return result.most_recent_acronym
        return '{0.most_recent_acronym} - {1}'.format(result, title)


class FacultyEntityAutocompleteView(PermissionRequiredMixin, autocomplete.Select2QuerySetView):
    login_url = 'access_denied'
    permission_required = 'partnership.can_access_partnerships'

    def get_queryset(self):
        qs = Entity.objects.annotate(
            most_recent_acronym=Subquery(
                EntityVersion.objects
                    .filter(entity=OuterRef('pk'))
                    .order_by('-start_date')
                    .values('acronym')[:1]
            ),
        )
        ucl_university = self.forwarded.get('ucl_university', None)
        if ucl_university:
            qs = qs.filter(entityversion__parent=ucl_university)
        else:
            return Entity.objects.none()
        qs = qs.annotate(
            is_valid=Exists(
                EntityVersion.objects
                    .filter(entity=OuterRef('pk'))
                    .exclude(end_date__lte=date.today())
            )
        ).filter(is_valid=True)
        if self.q:
            qs = qs.filter(most_recent_acronym__icontains=self.q)
        qs = qs.order_by('most_recent_acronym')
        return qs.distinct()

    def get_result_label(self, result):
        title = result.entityversion_set.latest("start_date").title
        return '{0.most_recent_acronym} - {1}'.format(result, title)


class UclUniversityAutocompleteView(FacultyAutocompleteView):
    login_url = 'access_denied'
    permission_required = 'partnership.can_access_partnerships'

    def get_queryset(self):
        queryset = super(UclUniversityAutocompleteView, self).get_queryset()
        queryset = queryset.filter(faculty_managements__isnull=False)
        return queryset


class UclUniversityLaboAutocompleteView(FacultyEntityAutocompleteView):
    login_url = 'access_denied'
    permission_required = 'partnership.can_access_partnerships'

    def get_queryset(self):
        queryset = super(UclUniversityLaboAutocompleteView, self).get_queryset()
        queryset = queryset.filter(entity_managements__isnull=False)
        return queryset


class PartnershipYearEntitiesAutocompleteView(PermissionRequiredMixin, autocomplete.Select2QuerySetView):
    login_url = 'access_denied'
    permission_required = 'partnership.can_access_partnerships'

    def get_queryset(self):
        faculty = self.forwarded.get('faculty', None)
        if faculty is not None:
            qs = Entity.objects.annotate(
                most_recent_acronym=Subquery(
                    EntityVersion.objects
                        .filter(entity=OuterRef('pk'))
                        .order_by('-start_date')
                        .values('acronym')[:1]
                ),
            ).filter(entityversion__parent=faculty)
        else:
            return Entity.objects.none()
        qs = qs.annotate(
            is_valid=Exists(
                EntityVersion.objects
                .filter(entity=OuterRef('pk'))
                .exclude(end_date__lte=date.today())
            )
        ).filter(is_valid=True)
        if self.q:
            qs = qs.filter(most_recent_acronym__icontains=self.q)
        return qs.distinct()

    def get_result_label(self, result):
        try:
            title = result.entityversion_set.latest("start_date").title
            return '{0.most_recent_acronym} - {1}'.format(result, title)
        except EntityVersion.DoesNotExist:
            return result.most_recent_acronym


class PartnershipYearOffersAutocompleteView(PermissionRequiredMixin, autocomplete.Select2QuerySetView):
    login_url = 'access_denied'
    permission_required = 'partnership.can_access_partnerships'

    def get_queryset(self):
        qs = EducationGroupYear.objects.filter(joint_diploma=True).select_related('academic_year')
        next_academic_year = \
            PartnershipConfiguration.get_configuration().get_current_academic_year_for_creation_modification()
        qs = qs.filter(academic_year=next_academic_year)
        # Education levels filter
        education_levels = self.forwarded.get('education_levels', None)
        if education_levels is not None:
            qs = qs.filter(education_group_type__partnership_education_levels__in=education_levels)
        else:
            return EducationGroupYear.objects.none()
        # Entities filter
        entities = self.forwarded.get('entities', None)
        if entities is not None:
            qs = qs.filter(Q(management_entity__in=entities) | Q(administration_entity__in=entities))
        else:
            faculty = self.forwarded.get('faculty', None)
            if faculty is not None:
                qs = qs.filter(
                    Q(management_entity=faculty) | Q(administration_entity=faculty)
                    | Q(management_entity__entityversion__parent=faculty)
                    | Q(administration_entity__entityversion__parent=faculty)
                )
            else:
                return EducationGroupYear.objects.none()
        # Query filter
        if self.q:
            qs = qs.filter(title__icontains=self.q)
        return qs.distinct('education_group').order_by()

    def get_result_label(self, result):
        return '{0.acronym} - {0.title}'.format(result)


# Partnership filters autocompletes

class PartnerAutocompletePartnershipsFilterView(PermissionRequiredMixin, autocomplete.Select2QuerySetView):
    login_url = 'access_denied'
    permission_required = 'partnership.can_access_partnerships'

    def get_queryset(self):
        qs = Partner.objects.filter(partnerships__isnull=False)
        if self.q:
            qs = qs.filter(name__icontains=self.q)
        return qs.distinct()


class PartnerEntityAutocompletePartnershipsFilterView(PermissionRequiredMixin, autocomplete.Select2QuerySetView):
    login_url = 'access_denied'
    permission_required = 'partnership.can_access_partnerships'

    def get_queryset(self):
        qs = PartnerEntity.objects.filter(partnerships__isnull=False)
        partner = self.forwarded.get('partner', None)
        if partner:
            qs = qs.filter(partner=partner)
        else:
            return PartnerEntity.objects.none()
        if self.q:
            qs = qs.filter(name__icontains=self.q)
        return qs.distinct()


class UclUniversityAutocompleteFilterView(UclUniversityAutocompleteView):
    login_url = 'access_denied'
    permission_required = 'partnership.can_access_partnerships'

    def get_queryset(self):
        qs = (
            Entity.objects
            .annotate(
                most_recent_acronym=Subquery(
                    EntityVersion.objects
                        .filter(entity=OuterRef('pk'))
                        .order_by('-start_date')
                        .values('acronym')[:1]
                ),
                is_valid=Exists(
                    EntityVersion.objects
                        .filter(entity=OuterRef('pk'))
                        .exclude(end_date__lte=date.today())
                ),
            )
            .filter(partnerships__isnull=False, is_valid=True)
        )
        if self.q:
            qs = qs.filter(most_recent_acronym__icontains=self.q)
        qs = qs.order_by('most_recent_acronym')
        return qs.distinct()


class UclUniversityLaboAutocompleteFilterView(UclUniversityLaboAutocompleteView):
    login_url = 'access_denied'
    permission_required = 'partnership.can_access_partnerships'

    def get_queryset(self):
        qs = super().get_queryset()
        ucl_university = self.forwarded.get('ucl_university', None)
        if ucl_university:
            qs = qs.filter(partnerships_labo__ucl_university=ucl_university)
        else:
            return Entity.objects.none()
        return qs.distinct()


class YearsEntityAutocompleteFilterView(FacultyEntityAutocompleteView):
    login_url = 'access_denied'
    permission_required = 'partnership.can_access_partnerships'

    def get_queryset(self):
        qs = super(YearsEntityAutocompleteFilterView, self).get_queryset()
        qs = qs.filter(partnerships_years__isnull=False)
        return qs


class UniversityOffersAutocompleteFilterView(PermissionRequiredMixin, autocomplete.Select2QuerySetView):
    login_url = 'access_denied'
    permission_required = 'partnership.can_access_partnerships'

    def get_queryset(self):
        qs = EducationGroupYear.objects.all().select_related('academic_year')
        next_academic_year = \
            PartnershipConfiguration.get_configuration().get_current_academic_year_for_creation_modification()
        qs = qs.filter(academic_year=next_academic_year)
        ucl_university = self.forwarded.get('ucl_university', None)
        education_level = self.forwarded.get('education_level', None)
        entity = self.forwarded.get('years_entity', None)
        if not ucl_university or not education_level:
            return EducationGroupYear.objects.none()
        if entity:
            qs = qs.filter(partnerships__entities=entity)
        else:
            qs = qs.filter(partnerships__partnership__ucl_university=ucl_university)
        qs = qs.filter(education_group_type__partnership_education_levels=education_level)
        if self.q:
            qs = qs.filter(title__icontains=self.q)
        return qs.distinct()

    def get_result_label(self, result):
        return '{0.acronym} - {0.title}'.format(result)
