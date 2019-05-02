from django.db import models
from django.db.models.aggregates import Count
from django.db.models.expressions import Subquery, OuterRef, Value, Exists, Case, When
from django.db.models.functions import Concat
from django.db.models.query import Prefetch
from django.db.models.query_utils import Q
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import generics
from rest_framework.generics import GenericAPIView
from rest_framework.permissions import AllowAny

from base.models.academic_year import AcademicYear
from base.models.entity import Entity
from base.models.entity_version import EntityVersion
from partnership.api.filters import PartnershipFilter
from partnership.api.serializers import PartnershipSerializer

from partnership.models import Partner, Partnership, PartnershipYearEducationField, PartnershipYear, \
    PartnershipConfiguration, PartnershipAgreement, Media


class PartnershipsMixinView(GenericAPIView):
    serializer_class = PartnershipSerializer
    permission_classes = (AllowAny,)

    def get_queryset(self):
        academic_year = PartnershipConfiguration.get_configuration().get_current_academic_year_for_api()

        return (
            Partnership.objects
            .select_related(
                'supervisor',
            ).prefetch_related(
                'contacts',
                Prefetch(
                    'medias',
                    queryset=Media.objects
                        .filter(visibility=Media.VISIBILITY_PUBLIC),
                    to_attr='public_medias',
                ),
                Prefetch(
                    'partner',
                    queryset=Partner.objects
                        .select_related('partner_type', 'contact_address__country')
                        .annotate(partnerships_count=Count('partnerships'))
                ),
                Prefetch(
                    'ucl_university',
                    queryset=Entity.objects
                    .annotate(
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
                Prefetch(
                    'ucl_university_labo',
                    queryset=Entity.objects
                    .annotate(
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
                Prefetch(
                    'years',
                    queryset=(
                        PartnershipYear.objects
                        .prefetch_related(
                            'education_fields', 'education_levels', 'entities', 'offers'
                        ).filter(academic_year=academic_year)
                    ),
                    to_attr='current_year_for_api',
                ),
            )
            .annotate(
                current_academic_year=Value(academic_year.id, output_field=models.AutoField()),
                validity_end_year=Subquery(
                    AcademicYear.objects
                    .filter(
                        partnership_agreements_end__partnership=OuterRef('pk'),
                        partnership_agreements_end__status=PartnershipAgreement.STATUS_VALIDATED
                    )
                    .order_by('-end_date')
                    .values('year')[:1]
                ),
            ).annotate(
                validity_years=Concat(
                    Value(academic_year.year),
                    Value('-'),
                    'validity_end_year',
                    output_field=models.CharField()
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
                sector_most_recent_acronym=Subquery(
                    EntityVersion.objects
                        .filter(entity__parent_of__entity=OuterRef('ucl_university__pk'))
                        .order_by('-start_date')
                        .values('acronym')[:1]
                ),
                has_in=Exists(
                    PartnershipAgreement.objects.filter(
                        partnership=OuterRef('pk'),
                        start_academic_year__year__lte=academic_year.year,
                        end_academic_year__year__gte=academic_year.year,
                    )
                ),
                subject_area_ordered=Subquery(  # For ordering only
                    PartnershipYearEducationField.objects
                    .filter(
                        partnershipyear__academic_year=academic_year,
                        partnershipyear__partnership=OuterRef('pk'),
                    )
                    .order_by('label')
                    .values('label')[:1]
                ),
                type_ordered=Subquery(  # For ordering only
                    PartnershipYear.objects
                    .filter(academic_year=academic_year, partnership=OuterRef('pk'))
                    .annotate(
                        type_ordered=Case(  # We can't make a Case directly as it will create several lines in the results
                            When(
                                (Q(is_sms=True)
                                | Q(is_smp=True)
                                | Q(is_smst=True))
                                & (Q(is_sta=True)
                                   | Q(is_stt=True)),
                                then=Value('a-student-staff')
                            ),
                            When(
                                Q(is_sms=True)
                                | Q(is_smp=True)
                                | Q(is_smst=True),
                                then=Value('b-student')
                            ),
                            When(
                                Q(is_sta=True)
                                | Q(is_stt=True),
                                then=Value('c-staff')
                            ),
                            default=Value('d-none'),
                            output_field=models.CharField(),
                        )
                    ).values('type_ordered')[:1]
                )
            )
            .filter(has_in=True)
            .distinct()
        )


class PartnershipsListView(PartnershipsMixinView, generics.ListAPIView):
    filter_backends = [DjangoFilterBackend]
    filterset_class = PartnershipFilter


class PartnershipsRetrieveView(PartnershipsMixinView, generics.RetrieveAPIView):
    lookup_field = 'uuid'