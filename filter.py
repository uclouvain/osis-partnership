import django_filters as filters
from django.db.models import Q, Exists, OuterRef, Max, Subquery
from django.db.models.functions import Now

from base.models.entity_version import EntityVersion
from partnership.forms import (
    PartnerFilterForm, PartnershipFilterForm,
    CustomNullBooleanSelect,
)
from partnership.models import (
    Partner, Partnership, PartnershipAgreement,
    AgreementStatus,
    PartnershipYear,
    Financing,
)


class PartnerAdminFilter(filters.FilterSet):
    ordering = filters.OrderingFilter(
        fields=(
            ('name', 'partner'),
            ('contact_address__country__name', 'country'),
            ('erasmus_code', 'erasmus_code'),
            ('partner_type__value', 'partner_type'),
            ('contact_address__city', 'city'),
            ('is_valid', 'is_valid'),
            ('is_actif', 'is_actif'),
        )
    )
    name = filters.CharFilter(lookup_expr='icontains')
    pic_code = filters.CharFilter(lookup_expr='icontains')
    erasmus_code = filters.CharFilter(lookup_expr='icontains')
    continent = filters.CharFilter(
        field_name='contact_address__country__continent',
    )
    country = filters.CharFilter(
        field_name='contact_address__country',
    )
    city = filters.CharFilter(
        field_name='contact_address__city',
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
        if value:
            return queryset.filter(
                (Q(start_date__isnull=True) & Q(end_date__isnull=True))
                | (Q(start_date__lte=Now()) & Q(end_date__gte=Now()))
            )
        else:
            return queryset.filter(
                Q(start_date__gt=Now()) | Q(end_date__lt=Now())
            )


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


class PartnershipAdminFilter(filters.FilterSet):
    ordering = filters.OrderingFilter(
        fields=(
            ('partner__name', 'partner'),
            ('partner__contact_address__country__name', 'country'),
            ('partner__contact_address__city', 'city'),
            ('ucl_university_parent_most_recent_acronym', 'ucl'),
        )
    )
    continent = filters.CharFilter(
        field_name='partner__contact_address__country__continent',
    )
    country = filters.CharFilter(
        field_name='partner__contact_address__country',
    )
    city = filters.CharFilter(field_name='partner__contact_address__city')
    partner_type = filters.CharFilter(field_name='partner__partner_type')
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
    partnership_type = filters.CharFilter(field_name='years__partnership_type')
    partnership_in = filters.CharFilter(method='filter_partnership_in')
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
    comment = filters.CharFilter(lookup_expr='icontains')

    class Meta:
        model = Partnership
        fields = [
            'ordering',
            'partner_type',
            'ucl_university',
            'ucl_university_labo',
            'education_level',
            'years_entity',
            'university_offer',
            'partner',
            'partner_entity',
            'partner_type',
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
            'partnership_type',
            'supervisor',
            'tags',
            'partnership_in',
            'partnership_ending_in',
            'partnership_valid_in',
            'partnership_not_valid_in',
            'partnership_with_no_agreements_in',
            'comment',
        ]

    def get_form_class(self):
        return PartnershipFilterForm

    @staticmethod
    def filter_years_entity(queryset, name, value):
        if value:
            queryset = queryset.filter(
                Q(years__entities=value) | Q(years__entities__isnull=True)
            )
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
                has_valid=Exists(
                    PartnershipAgreement.objects.filter(
                        partnership=OuterRef('pk'),
                        status=AgreementStatus.VALIDATED.name,
                        start_academic_year__start_date__lte=value.start_date,
                        end_academic_year__end_date__gte=value.end_date,
                    )
                )
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


class PartnershipAgreementAdminFilter(PartnershipAdminFilter):
    ordering = filters.OrderingFilter(
        fields=(
            ('partnership__partner__name', 'partner'),
            ('partnership__partner__contact_address__country__name', 'country'),
            ('partnership__partner__contact_address__city', 'city'),
            ('partnership__ucl_university_parent_most_recent_acronym', 'ucl'),
        )
    )

    @property
    def qs(self):
        queryset = (
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
                partnership__in=super().qs
            ).select_related(
                'partnership__partner__contact_address__country',
                'partnership__supervisor',
                'partnership__ucl_university',
                'partnership__ucl_university_labo',
                'start_academic_year',
                'end_academic_year',
            )
        )

        # Reapply ordering
        if self.is_bound:
            ordering = self.form.cleaned_data.get('ordering')
            queryset = self.filters['ordering'].filter(queryset, ordering)

        return queryset
