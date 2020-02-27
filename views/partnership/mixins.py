from copy import copy

from django.contrib import messages
from django.db.models import Q, Exists, OuterRef, Max, Subquery
from django.http import HttpResponseRedirect
from django.utils.functional import cached_property
from django.utils.translation import gettext_lazy as _
from django.views.generic.edit import FormMixin
from django.views.generic.list import MultipleObjectMixin

from base.models.academic_year import current_academic_year, AcademicYear
from base.models.entity_version import EntityVersion
from partnership.forms import (
    PartnershipForm, PartnershipYearForm, PartnershipFilterForm,
)
from partnership.models import (
    Partnership, PartnershipConfiguration, UCLManagementEntity,
    PartnershipAgreement, PartnershipYear, AgreementStatus
)
from partnership.utils import user_is_gf, user_is_adri


__all__ = [
    'PartnershipFormMixin',
    'PartnershipListFilterMixin',
]


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
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user
        return kwargs

    def get_context_data(self, **kwargs):
        if 'form_year' not in kwargs:
            kwargs['form_year'] = self.get_form_year()
        kwargs['current_academic_year'] = current_academic_year()

        return super().get_context_data(**kwargs)

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


class PartnershipListFilterMixin(FormMixin, MultipleObjectMixin):
    form_class = PartnershipFilterForm
    login_url = 'access_denied'

    def get(self, *args, **kwargs):
        if not self.request.GET and user_is_gf(self.request.user):
            university = self.request.user.person.partnershipentitymanager_set.first().entity
            if Partnership.objects.filter(ucl_university=university).exists():
                return HttpResponseRedirect(
                    '?ucl_university={0}'.format(university.pk)
                )
        return super().get(*args, **kwargs)

    def get_context_object_name(self, object_list):
        if self.is_agreements:
            return 'agreements'
        return 'partnerships'

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        if self.request.GET:
            # Remove empty value from GET
            data = copy(self.request.GET)
            for key, value in list(data.items()):
                if value == '':
                    del data[key]
            kwargs['data'] = data
        return kwargs

    def get_form(self, form_class=None):
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
                        partnership=OuterRef('pk'),
                        status=AgreementStatus.VALIDATED.name,
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
                        status=AgreementStatus.VALIDATED.name,
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
                            partnership_agreements_end__status=AgreementStatus.VALIDATED.name,
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
