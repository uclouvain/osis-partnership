import django_filters as filters
from django.db.models import Exists, Max, OuterRef, Q
from django.utils.translation import gettext_lazy as _

from base.models.entity_version import EntityVersion
from base.utils.cte import CTESubquery
from partnership.forms import (
    PartnerFilterForm, PartnershipFilterForm,
    CustomNullBooleanSelect,
)
from partnership.models import (
    AgreementStatus,
    Partner,
    Partnership,
    PartnershipAgreement,
    PartnershipYear,
)


def filter_pk_from_annotation(queryset, name, value):
    return queryset.filter(**{name: value.pk})


class PartnerAdminFilter(filters.FilterSet):
    ordering = filters.OrderingFilter(
        fields=(
            ('organization__name', 'partner'),
            ('country_name', 'country'),
            ('erasmus_code', 'erasmus_code'),
            ('organization__type', 'partner_type'),
            ('city', 'city'),
            ('is_valid', 'is_valid'),
            ('is_actif', 'is_actif'),
        )
    )
    name = filters.CharFilter(
        field_name='organization__name',
        lookup_expr='icontains',
    )
    partner_type = filters.CharFilter(field_name='organization__type')
    pic_code = filters.CharFilter(lookup_expr='icontains')
    erasmus_code = filters.CharFilter(lookup_expr='icontains')
    continent = filters.CharFilter(
        field_name='country_continent_id',
        method=filter_pk_from_annotation,
    )
    country = filters.CharFilter(
        field_name='country_id',
        method=filter_pk_from_annotation,
    )
    city = filters.CharFilter(
        field_name='city',
        lookup_expr='iexact',
    )
    is_actif = filters.BooleanFilter(
        method='filter_is_actif',
    )

    class Meta:
        model = Partner
        fields = [
            'ordering',
            'name',
            'partner_type',
            'pic_code',
            'erasmus_code',
            'is_ies',
            'is_valid',
            'is_actif',
            'tags',
            'continent',
            'country',
            'city',
        ]

    def get_form_class(self):
        return PartnerFilterForm

    @staticmethod
    def filter_is_actif(queryset, name, value):
        return queryset.annotate_dates(filter_value=value)


class FinancingOrderingFilter(filters.OrderingFilter):
    def filter(self, qs, value):
        if not value:
            return qs
        ordering = value[0]
        if ordering.lstrip('-') in ['financing_name', 'financing_url']:
            return qs.order_by(ordering, 'name')
        elif ordering.lstrip('-') == 'name':
            return qs.order_by(ordering, 'iso_code')


class FinancingAdminFilter(filters.FilterSet):
    ordering = FinancingOrderingFilter(
        fields=(
            ('financing_name', 'financing_name'),
            ('financing_url', 'financing_url'),
            ('name', 'name'),
        )
    )


class MultipleOrderingFilter(filters.OrderingFilter):
    def __init__(self, *args, multiples=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.special_ordering = multiples if multiples is not None else {}

    def filter(self, qs, value):
        if not value:
            return qs
        ordering = value[0]
        field = ordering.lstrip('-')
        if field in self.special_ordering.keys():
            fields = self.special_ordering[field]
            return qs.order_by(
                *['-' + f if ordering[0] == '-' else f for f in fields]
            )
        return super().filter(qs, value)


class PartnershipAdminFilter(filters.FilterSet):
    ordering = MultipleOrderingFilter(
        fields=(
            ('partner__organization__name', 'partner'),
            ('city', 'city'),
            ('acronym_path', 'ucl')
        ),
        multiples={
            'country': [
                'country_name',
                'city',
                'partner__organization__name'
            ],
        },
    )
    continent = filters.CharFilter(
        field_name='country_continent_id',
        method=filter_pk_from_annotation
    )
    country = filters.ModelChoiceFilter(
        field_name='country_id',
        method=filter_pk_from_annotation,
    )
    city = filters.CharFilter()
    ucl_entity = filters.ModelChoiceFilter(method='filter_ucl_entity')
    # This is a noop filter, as its logic is in filter_ucl_entity()
    ucl_entity_with_child = filters.BooleanFilter(method=lambda qs, *_: qs)
    partner_type = filters.CharFilter(field_name='partner__organization__type')
    education_level = filters.CharFilter(field_name='years__education_levels')
    education_field = filters.CharFilter(field_name='years__education_fields')
    years_entity = filters.CharFilter(method='filter_years_entity')
    university_offer = filters.CharFilter(method='filter_university_offer')
    partner_tags = filters.CharFilter(method='filter_partner_tags')
    erasmus_code = filters.CharFilter(
        field_name='partner__erasmus_code',
        lookup_expr='icontains',
    )
    use_egracons = filters.BooleanFilter(
        field_name='partner__use_egracons',
        widget=CustomNullBooleanSelect()
    )
    is_sms = filters.BooleanFilter(
        field_name='years__is_sms',
        widget=CustomNullBooleanSelect(),
    )
    is_smp = filters.BooleanFilter(
        field_name='years__is_smp',
        widget=CustomNullBooleanSelect(),
    )
    is_sta = filters.BooleanFilter(
        field_name='years__is_sta',
        widget=CustomNullBooleanSelect(),
    )
    is_stt = filters.BooleanFilter(
        field_name='years__is_stt',
        widget=CustomNullBooleanSelect(),
    )
    is_smst = filters.BooleanFilter(
        field_name='years__is_smst',
        widget=CustomNullBooleanSelect(),
    )
    funding_type = filters.ModelChoiceFilter(field_name='years__funding_type')
    funding_program = filters.ModelChoiceFilter(
        field_name='years__funding_type__program',
    )
    funding_source = filters.ModelChoiceFilter(
        field_name='years__funding_type__program__source',
    )
    partnership_in = filters.CharFilter(method='filter_partnership_in')
    subtype = filters.CharFilter(field_name='years__subtype')
    partnership_ending_in = filters.CharFilter(
        method='filter_partnership_ending_in'
    )
    partnership_valid_in = filters.CharFilter(
        method='filter_partnership_valid_in'
    )
    partnership_not_valid_in = filters.CharFilter(
        method='filter_partnership_not_valid_in'
    )
    partnership_with_no_agreements_in = filters.CharFilter(
        method='filter_partnership_with_no_agreements_in'
    )
    partnership_special_dates_type = filters.CharFilter(
        method='filter_partnership_special_dates'
    )
    # Noop filter, their logic is in filter_partnership_special_dates()
    partnership_special_dates_0 = filters.DateFilter(method=lambda qs, *_: qs)
    partnership_special_dates_1 = filters.DateFilter(method=lambda qs, *_: qs)
    comment = filters.CharFilter(lookup_expr='icontains')
    is_public = filters.BooleanFilter(widget=CustomNullBooleanSelect())

    class Meta:
        model = Partnership
        fields = [
            'ordering',
            'partnership_type',
            'partner_type',
            'ucl_entity',
            'education_level',
            'years_entity',
            'university_offer',
            'partner',
            'partner_entity',
            'erasmus_code',
            'use_egracons',
            'continent',
            'country',
            'city',
            'partner_tags',
            'education_field',
            'is_sms',
            'is_smp',
            'is_sta',
            'is_stt',
            'is_smst',
            'funding_type',
            'funding_program',
            'funding_source',
            'partnership_type',
            'supervisor',
            'tags',
            'partnership_in',
            'partnership_ending_in',
            'partnership_valid_in',
            'partnership_not_valid_in',
            'partnership_with_no_agreements_in',
            'partnership_special_dates_type',
            'partnership_special_dates_0',
            'partnership_special_dates_1',
            'comment',
            'is_public',
        ]

    @property
    def form(self):
        if not hasattr(self, '_form'):
            if self.is_bound:
                self._form = PartnershipFilterForm(
                    self.data,
                    user=self.request.user,
                    prefix=self.form_prefix,
                )
            else:
                self._form = PartnershipFilterForm(
                    user=self.request.user,
                    prefix=self.form_prefix,
                )
        return self._form

    @staticmethod
    def filter_years_entity(queryset, name, value):
        if value:
            queryset = queryset.filter(
                Q(years__entities=value) | Q(years__entities__isnull=True)
            )
        return queryset

    def filter_ucl_entity(self, queryset, name, value):
        if value:
            if self.form.cleaned_data.get('ucl_entity_with_child', False):
                # Allow all children of entity too
                cte = EntityVersion.objects.with_parents(entity_id=value.pk)
                qs = cte.queryset().with_cte(cte).values('entity_id')
                queryset = queryset.filter(ucl_entity__in=qs)
            else:
                queryset = queryset.filter(ucl_entity=value)

        return queryset

    @staticmethod
    def filter_partner_tags(queryset, name, value):
        if value:
            queryset = queryset.filter(partner__tags__in=value)
        return queryset

    @staticmethod
    def filter_university_offer(queryset, name, value):
        if value:
            queryset = queryset.filter(
                Q(years__offers=value) | Q(years__offers__isnull=True)
            )
        return queryset

    @staticmethod
    def filter_partnership_in(queryset, name, value):
        if value:
            queryset = queryset.annotate(
                has_in=Exists(
                    PartnershipAgreement.objects.filter(
                        partnership=OuterRef('pk'),
                        start_academic_year__start_date__lte=value.start_date,
                        end_academic_year__end_date__gte=value.end_date,
                    )
                )
            ).filter(has_in=True)
        return queryset

    @staticmethod
    def filter_partnership_ending_in(queryset, name, value):
        if value:
            queryset = (
                queryset.annotate(
                    ending_date=Max('agreements__end_academic_year__end_date')
                ).filter(ending_date=value.end_date)
            )
        return queryset

    @staticmethod
    def filter_partnership_valid_in(queryset, name, value):
        if value:
            queryset = queryset.annotate(
                has_valid=Exists(PartnershipAgreement.objects.filter(
                    partnership=OuterRef('pk'),
                    status=AgreementStatus.VALIDATED.name,
                    start_academic_year__start_date__lte=value.start_date,
                    end_academic_year__end_date__gte=value.end_date,
                ))
            ).filter(has_valid=True)
        return queryset

    @staticmethod
    def filter_partnership_not_valid_in(queryset, name, value):
        if value:
            queryset = queryset.annotate(
                not_valid_in_has_agreements=Exists(
                    PartnershipAgreement.objects.filter(
                        partnership=OuterRef('pk'),
                    ).filter(
                        start_academic_year__start_date__lte=value.start_date,
                        end_academic_year__end_date__gte=value.end_date,
                    ),
                ),
                not_valid_in_has_valid_agreements=Exists(
                    PartnershipAgreement.objects.filter(
                        partnership=OuterRef('pk'),
                    ).filter(
                        status=AgreementStatus.VALIDATED.name,
                        start_academic_year__start_date__lte=value.start_date,
                        end_academic_year__end_date__gte=value.end_date,
                    ),
                )
            ).filter(
                not_valid_in_has_agreements=True,
                not_valid_in_has_valid_agreements=False,
            )
        return queryset

    @staticmethod
    def filter_partnership_with_no_agreements_in(queryset, name, value):
        if value:
            queryset = queryset.annotate(
                no_agreements_in_has_years=Exists(
                    PartnershipYear.objects.filter(
                        partnership=OuterRef('pk'),
                        academic_year=value,
                    )
                ),
                no_agreements_in_has_agreements=Exists(
                    PartnershipAgreement.objects.filter(
                        partnership=OuterRef('pk'),
                        start_academic_year__start_date__lte=value.start_date,
                        end_academic_year__end_date__gte=value.end_date,
                    )
                ),
            ).filter(
                no_agreements_in_has_years=True,
                no_agreements_in_has_agreements=False,
            )
        return queryset

    def filter_partnership_special_dates(self, queryset, name, value):
        # Prevent filtering on partnership when agreement filter
        if isinstance(self, PartnershipAgreementAdminFilter) and queryset.model == Partnership:
            return queryset

        date_from = self.form.cleaned_data['partnership_special_dates_0']
        date_to = self.form.cleaned_data.get('partnership_special_dates_1')
        if value == 'ongoing':
            if not date_to:
                # start_date < filter_date < end_date
                return queryset.filter(
                    start_date__lte=date_from,
                    end_date__gte=date_from,
                )
            # periods must intersect
            return queryset.filter(
                Q(start_date__lte=date_from, end_date__gte=date_from)
                | Q(start_date__lte=date_to, end_date__gte=date_to),
            )
        elif value == 'stopping':
            # filter_date_0 < end_date < filter_date_1
            return queryset.filter(
                end_date__gte=date_from,
                end_date__lte=date_to,
            )


class PartnershipAgreementAdminFilter(PartnershipAdminFilter):
    ordering = MultipleOrderingFilter(
        fields=(
            ('partnership__partner__organization__name', 'partner'),
            ('country', 'country'),
            ('city', 'city'),
            ('acronym_path', 'ucl'),
        ),
        multiples={
            'country': [
                'country_name',
                'city',
                'partnership__partner__organization__name',
            ],
        }
    )

    @property
    def form(self):
        form = super().form
        form.fields['partnership_special_dates_type'].label = _("Agreements")
        return form

    @property
    def qs(self):
        # See also Partnership.objects.add_acronyms()
        queryset = (
            PartnershipAgreement.objects
            .annotate_partner_address(
                'country__name',
                'city',
            )
            # TODO remove when Entity city field is dropped (conflict)
            .defer("partnership__ucl_entity__city")
            .annotate(
                acronym_path=CTESubquery(
                    EntityVersion.objects.with_acronym_path(
                        entity_id=OuterRef('partnership__ucl_entity__pk')
                    ).values('acronym_path')[:1]
                ),
                title_path=CTESubquery(
                    EntityVersion.objects.with_acronym_path(
                        entity_id=OuterRef('partnership__ucl_entity__pk')
                    ).values('title_path')[:1]
                ),
            ).filter(
                partnership__in=super().qs
            ).select_related(
                'partnership__supervisor',
                'partnership__ucl_entity__uclmanagement_entity__academic_responsible',
                'partnership__partner__organization',
                'start_academic_year',
                'end_academic_year',
            )
        )

        # Apply special filtering if needed
        special_filter = self.data.get('partnership_special_dates_type')
        if special_filter:
            queryset = self.filter_partnership_special_dates(
                queryset, '', special_filter,
            )

        # Reapply ordering
        if self.is_bound:
            ordering = self.form.cleaned_data.get('ordering')
            queryset = self.filters['ordering'].filter(queryset, ordering)

        return queryset
