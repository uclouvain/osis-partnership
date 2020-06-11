from django.db import models
from django.db.models.aggregates import Count
from django.db.models.expressions import F, OuterRef, Subquery, Value
from django.db.models.functions import Concat, Now
from django.db.models.query import Prefetch
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import generics
from rest_framework.generics import GenericAPIView
from rest_framework.permissions import AllowAny

from base.models.academic_year import AcademicYear
from base.models.entity import Entity
from base.models.entity_version import EntityVersion
from partnership.models import (
    AgreementStatus,
    Financing,
    Media,
    Partner,
    Partnership,
    PartnershipAgreement,
    PartnershipConfiguration,
    PartnershipYear,
)
from ..filters import PartnershipFilter
from ..serializers import PartnershipSerializer

__all__ = [
    'PartnershipsRetrieveView',
    'PartnershipsListView',
]


class PartnershipsMixinView(GenericAPIView):
    serializer_class = PartnershipSerializer
    permission_classes = (AllowAny,)

    def get_serializer_context(self):
        return {
            **super().get_serializer_context(),
            'request': self.request
        }

    def get_queryset(self):
        academic_year = PartnershipConfiguration.get_configuration().get_current_academic_year_for_api()

        return (
            Partnership.objects
            .filter_for_api(academic_year)
            .add_acronyms()
            .annotate_partner_address(
                'country__continent__name',
                'country__iso_code',
                'country__name',
                'country_id',
                'city',
            )
            .select_related(
                'supervisor',
                'partner_entity',
            ).prefetch_related(
                'contacts',
                Prefetch(
                    'medias',
                    queryset=Media.objects.select_related('type').filter(
                        is_visible_in_portal=True
                    ),
                ),
                Prefetch(
                    'partner',
                    queryset=Partner.objects.annotate_address(
                            'country__iso_code',
                            'country__name',
                            'city',
                        ).annotate_website().prefetch_related(
                            Prefetch(
                                'medias',
                                queryset=Media.objects.filter(
                                    is_visible_in_portal=True
                                ).select_related('type')
                            ),
                        ).annotate(
                            partnerships_count=Count('partnerships'),
                        )
                ),
                Prefetch(
                    'ucl_entity',
                    queryset=Entity.objects
                    .select_related(
                        'uclmanagement_entity__academic_responsible',
                        'uclmanagement_entity__administrative_responsible',
                        'uclmanagement_entity__contact_out_person',
                        'uclmanagement_entity__contact_in_person',
                    )
                    .annotate(
                        most_recent_acronym=Subquery(
                            EntityVersion.objects.filter(
                                entity=OuterRef('pk')
                            ).order_by('-start_date').values('acronym')[:1]
                        ),
                        most_recent_title=Subquery(
                            EntityVersion.objects.filter(
                                entity=OuterRef('pk')
                            ).order_by('-start_date').values('title')[:1]
                        ),
                    )
                ),
                Prefetch(
                    'years',
                    queryset=(
                        PartnershipYear.objects
                        .select_related(
                            'academic_year',
                            'subtype',
                            'funding_source',
                            'funding_program',
                            'funding_type',
                        )
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
                                    most_recent_title=Subquery(
                                        EntityVersion.objects
                                        .filter(entity=OuterRef('pk'))
                                        .order_by('-start_date')
                                        .values('title')[:1]
                                    ),
                                )
                            ),
                            'education_fields',
                            'education_levels',
                            'offers',
                            'missions',
                        ).filter(academic_year=academic_year)
                    ),
                    to_attr='current_year_for_api',
                ),
                Prefetch(
                    'agreements',
                    queryset=(
                        PartnershipAgreement.objects
                        .select_related('media')
                        .filter(status=AgreementStatus.VALIDATED.name)
                        .filter(
                            start_academic_year__year__lte=academic_year.year,
                            end_academic_year__year__gte=academic_year.year,
                        )
                    ),
                    to_attr='valid_current_agreements',
                ),
            )
            .annotate(
                validity_end_year=Subquery(
                    AcademicYear.objects
                    .filter(
                        partnership_agreements_end__partnership=OuterRef('pk'),
                        partnership_agreements_end__status=AgreementStatus.VALIDATED.name
                    )
                    .order_by('-end_date')
                    .values('year')[:1]
                ),
                agreement_start=Subquery(
                    PartnershipAgreement.objects.filter(
                        partnership=OuterRef('pk'),
                        start_date__lte=Now(),
                        end_date__gte=Now(),
                    ).order_by('-end_date').values('start_date')[:1]
                ),
                agreement_end=Subquery(
                    PartnershipAgreement.objects.filter(
                        partnership=OuterRef('pk'),
                        start_date__lte=Now(),
                        end_date__gte=Now(),
                    ).order_by('-end_date').values('end_date')[:1]
                ),
            ).annotate(
                validity_years=Concat(
                    Value(academic_year.year),
                    Value('-'),
                    F('validity_end_year') + 1,
                    output_field=models.CharField()
                ),
                agreement_year_status=Subquery(
                    PartnershipAgreement.objects
                    .filter(
                        partnership=OuterRef('pk'),
                        start_academic_year__year__lte=academic_year.year,
                        end_academic_year__year__gte=academic_year.year,
                    )
                    .order_by('-end_academic_year__year')
                    .values('status')[:1]
                ),
                agreement_status=Subquery(
                    PartnershipAgreement.objects
                    .filter(
                        partnership=OuterRef('pk'),
                        start_academic_year__year__lte=academic_year.year,
                        end_academic_year__year__gte=academic_year.year,
                    )
                    .order_by('-end_academic_year__year')
                    .values('status')[:1]
                ),
                funding_name=Subquery(
                    Financing.objects.filter(
                        academic_year=academic_year,
                        countries=OuterRef('country_id'),
                    ).values('type__name')[:1]
                ),
                funding_url=Subquery(
                    Financing.objects.filter(
                        academic_year=academic_year,
                        countries=OuterRef('country_id'),
                    ).values('type__url')[:1]
                ),
            )
            .distinct()
        )


class PartnershipsListView(PartnershipsMixinView, generics.ListAPIView):
    filter_backends = [DjangoFilterBackend]
    filterset_class = PartnershipFilter


class PartnershipsRetrieveView(PartnershipsMixinView, generics.RetrieveAPIView):
    lookup_field = 'uuid'
