from django.contrib.gis.geos import Polygon
from django.db.models import Exists, OuterRef, Q, Case, When, Subquery, F
from django.utils.translation import gettext_lazy as _
from django_filters import rest_framework as filters

from base.models.entity_version import EntityVersion
from partnership.models import (
    Financing, Partnership, UCLManagementEntity,
    PartnershipType, PartnershipYear, FundingSource, FundingProgram,
    FundingType,
)


def filter_funding(year_field='', lookup=''):
    def inner(qs, name, value):
        # We need at least source to check if funding is set for mobility
        qs = qs.annotate(
            funding_source=Subquery(PartnershipYear.objects.filter(
                partnership=OuterRef('pk'),
                academic_year=OuterRef('current_academic_year'),
            ).values('funding_source_id')[:1]),
        )
        annotation_to_search_on = 'funding_source'

        if year_field != 'funding_source_id':
            # And if we don't search on source, we need the other value
            qs = qs.annotate(
                funding_value=Subquery(PartnershipYear.objects.filter(
                    partnership=OuterRef('pk'),
                    academic_year=OuterRef('current_academic_year'),
                ).values(year_field)[:1])
            )
            annotation_to_search_on = 'funding_value'

        return qs.annotate_partner_address('country_id').annotate(
            search_id=Case(
                # If mobility, take financing if funding not set
                When(partnership_type=PartnershipType.MOBILITY.name,
                     funding_source__isnull=True,
                     then=Subquery(Financing.objects.filter(
                         **{lookup: value.pk},
                         countries=OuterRef('country_id'),
                         academic_year=OuterRef('current_academic_year'),
                     ).values(lookup)[:1])),
                default=F(annotation_to_search_on))
        ).filter(search_id=value.pk)
    return inner


class PartnershipFilter(filters.FilterSet):
    continent = filters.CharFilter(
        field_name='country_continent_name',
        lookup_expr='iexact'
    )
    country = filters.CharFilter(
        field_name='country_iso_code',
        lookup_expr='iexact',
    )
    city = filters.CharFilter(field_name='city', lookup_expr='iexact')
    partner = filters.UUIDFilter(field_name='partner__uuid')

    ucl_entity = filters.UUIDFilter(method='filter_ucl_entity')
    # This is a noop filter, as its logic is in filter_ucl_entity()
    with_children = filters.BooleanFilter(method=lambda qs, *_: qs)

    type = filters.CharFilter(field_name='partnership_type')
    education_level = filters.CharFilter(
        field_name='years__education_levels__code',
    )

    supervisor = filters.UUIDFilter(
        label=_('partnership_supervisor'),
        method='filter_supervisor',
    )
    tag = filters.CharFilter(field_name='tags__value')
    partner_tag = filters.CharFilter(field_name='partner__tags__value')

    # Depends on the current year
    education_field = filters.UUIDFilter(
        label=_('education_field'),
        field_name='years__education_fields__uuid',
    )
    offer = filters.UUIDFilter(field_name='years__offers__uuid')
    mobility_type = filters.ChoiceFilter(
        label=_('mobility_type'),
        choices=(('student', "Student"), ('staff', "Staff")),
        method='filter_mobility_type',
    )
    funding_source = filters.ModelChoiceFilter(
        queryset=FundingSource.objects.all(),
        method=filter_funding('funding_source_id', 'type__program__source_id'),
    )
    funding_program = filters.ModelChoiceFilter(
        queryset=FundingProgram.objects.all(),
        method=filter_funding('funding_program_id', 'type__program_id'),
    )
    funding_type = filters.ModelChoiceFilter(
        queryset=FundingType.objects.all(),
        method=filter_funding('funding_type_id', 'type_id'),
    )

    bbox = filters.CharFilter(method='filter_bbox')

    class Meta:
        model = Partnership
        fields = [
            'continent', 'country', 'city', 'partner',
            'ucl_entity',
            'supervisor', 'education_field', 'mobility_type',
            'type', 'education_level',
        ]

    def filter_ucl_entity(self, queryset, name, value):
        if self.form.cleaned_data.get('with_children', True):
            # Allow all children of entity too
            cte = EntityVersion.objects.with_parents(entity__uuid=value)
            qs = cte.queryset().with_cte(cte).values('entity_id')
            return queryset.filter(ucl_entity__in=qs)
        else:
            return queryset.filter(ucl_entity__uuid=value)

    @staticmethod
    def filter_supervisor(queryset, name, value):
        return queryset.annotate(
            has_supervisor_with_entity=Exists(
                UCLManagementEntity.objects.filter(
                    entity=OuterRef('ucl_entity'),
                    academic_responsible__uuid=value,
                )
            ),
        ).filter(
            Q(supervisor__uuid=value)
            | Q(supervisor__isnull=True, has_supervisor_with_entity=True)
        )

    @staticmethod
    def filter_mobility_type(queryset, name, value):
        if value == 'student':
            return queryset.filter(
                Q(years__is_sms=True)
                | Q(years__is_smst=True)
                | Q(years__is_smp=True)
            )
        else:
            return queryset.filter(
                Q(years__is_stt=True) | Q(years__is_sta=True)
            )

    @staticmethod
    def filter_bbox(queryset, name, value):
        bbox = Polygon.from_bbox(value.split(','))
        return queryset.filter(location__contained=bbox)
