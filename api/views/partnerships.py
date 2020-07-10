from datetime import datetime

from django.conf import settings
from django.db import models
from django.db.models.aggregates import Count
from django.db.models.expressions import Subquery, OuterRef, Value, Exists, Case, When, F
from django.db.models.functions import Concat
from django.db.models.query import Prefetch
from django.db.models.query_utils import Q
from django.utils.translation import get_language
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import generics
from rest_framework.generics import GenericAPIView
from rest_framework.permissions import AllowAny

from base.models.academic_year import AcademicYear
from base.models.entity import Entity
from base.models.entity_version import EntityVersion
from partnership.models import (
    Financing,
    Media,
    Partner,
    Partnership,
    PartnershipAgreement,
    PartnershipConfiguration,
    PartnershipType,
    PartnershipYear,
    AgreementStatus,
)
from reference.models.domain_isced import DomainIsced
from ..filters import PartnershipFilter
from ..serializers import PartnershipSerializer


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

        label = 'title_fr' if get_language() == settings.LANGUAGE_CODE_FR else 'title_en'
        return (
            Partnership.objects
            .add_acronyms()
            .select_related(
                'supervisor',
                'partner_entity',
            ).prefetch_related(
                'contacts',
                Prefetch(
                    'medias',
                    queryset=Media.objects
                        .select_related('type')
                        .filter(is_visible_in_portal=True),
                ),
                Prefetch(
                    'partner',
                    queryset=Partner.objects
                        .annotate_website()
                        .select_related('contact_address__country')
                        .prefetch_related(
                            Prefetch(
                                'medias',
                                queryset=Media.objects
                                    .filter(is_visible_in_portal=True)
                                    .select_related('type')
                            ),
                        )
                        .annotate(
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
                        .select_related('academic_year')
                        .prefetch_related(
                            Prefetch(
                                'entities',
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
                            'education_fields',
                            'education_levels',
                            'offers',
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
                current_academic_year=Value(academic_year.id, output_field=models.AutoField()),
                validity_end_year=Subquery(
                    AcademicYear.objects
                    .filter(
                        partnership_agreements_end__partnership=OuterRef('pk'),
                        partnership_agreements_end__status=AgreementStatus.VALIDATED.name
                    )
                    .order_by('-end_date')
                    .values('year')[:1]
                ),
            ).annotate(
                validity_years=Concat(
                    Value(academic_year.year),
                    Value('-'),
                    F('validity_end_year') + 1,
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
                has_years_in=Exists(
                    PartnershipYear.objects.filter(
                        partnership=OuterRef('pk'),
                        academic_year=academic_year,
                    )
                ),
                has_valid_agreement_in_current_year=Exists(
                    PartnershipAgreement.objects.filter(
                        partnership=OuterRef('pk'),
                        status=AgreementStatus.VALIDATED.name,
                        start_academic_year__year__lte=academic_year.year,
                        end_academic_year__year__gte=academic_year.year,
                    )
                ),
                subject_area_ordered=Subquery(  # For ordering only
                    DomainIsced.objects
                    .filter(
                        partnershipyear__academic_year=academic_year,
                        partnershipyear__partnership=OuterRef('pk'),
                    )
                    .order_by(label)
                    .values(label)[:1]
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
                ),
                funding_name=Subquery(
                    Financing.objects.filter(
                        academic_year=academic_year,
                        countries=OuterRef('partner__contact_address__country_id'),
                    ).values('type__name')[:1]
                ),
                funding_url=Subquery(
                    Financing.objects.filter(
                        academic_year=academic_year,
                        countries=OuterRef('partner__contact_address__country_id'),
                    ).values('type__url')[:1]
                ),
            )
            .filter(
                Q(has_valid_agreement_in_current_year=True)
                | Q(partnership_type=PartnershipType.PROJECT.name),
                is_public=True,
                has_years_in=True,
                years__academic_year=F('current_academic_year'),  # From annotation
            )
            .distinct()
        )


class PartnershipsListView(PartnershipsMixinView, generics.ListAPIView):
    filter_backends = [DjangoFilterBackend]
    filterset_class = PartnershipFilter


class PartnershipsRetrieveView(PartnershipsMixinView, generics.RetrieveAPIView):
    lookup_field = 'uuid'
