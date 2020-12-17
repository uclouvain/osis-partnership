from django.contrib.postgres.aggregates import StringAgg
from django.db import models
from django.db.models.aggregates import Count
from django.db.models.expressions import (
    F, OuterRef, Subquery, Value,
)
from django.db.models.functions import Concat, Now, Right, Cast
from django.db.models.query import Prefetch
from django.http import JsonResponse
from django.urls import reverse
from django.utils.timezone import now
from django.utils.translation import gettext_lazy as _
from django_filters.rest_framework import DjangoFilterBackend
from django_filters.views import FilterMixin
from rest_framework import generics
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
from ...views import ExportView

__all__ = [
    'PartnershipsRetrieveView',
    'PartnershipsListView',
    'PartnershipExportView',
    'partnership_get_export_url',
]


class PartnershipsMixinView:
    serializer_class = PartnershipSerializer
    permission_classes = (AllowAny,)

    def get_serializer_context(self):
        return {
            **super().get_serializer_context(),
            'request': self.request
        }

    def get_queryset(self):
        academic_year = PartnershipConfiguration.get_configuration().get_current_academic_year_for_api()
        academic_year_repr = Concat(
            Cast(F('academic_year__year'), models.CharField()),
            Value('-'),
            Right(
                Cast(
                    F('academic_year__year') + 1,
                    output_field=models.CharField()
                ),
                2
            ),
        )

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
                'location',
            )
            .select_related(
                'subtype',
                'supervisor',
                'partner_entity',
            ).prefetch_related(
                'contacts',
                'missions',
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
                        ).filter(academic_year=academic_year)
                    ),
                    to_attr='current_year_for_api',
                ),
                Prefetch(
                    'agreements',
                    queryset=(
                        PartnershipAgreement.objects
                        .select_related('media', 'end_academic_year')
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
                start_year=Subquery(
                    PartnershipYear.objects.filter(
                        partnership=OuterRef('pk'),
                    ).annotate(
                        name=academic_year_repr
                    ).order_by('academic_year').values('name')[:1]
                ),
                end_year=Subquery(
                    PartnershipYear.objects.filter(
                        partnership=OuterRef('pk'),
                    ).annotate(
                        name=academic_year_repr
                    ).order_by('-academic_year').values('name')[:1]
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


def partnership_get_export_url(request):  # pragma: no cover
    # TODO: Fix when authentication is done in ESB (use already X-Forwarded-Host) / Shibb
    url = reverse('partnership_api_v1:partnerships:export')
    return JsonResponse({
        'url': '{scheme}://{host}{path}'.format(
            scheme=request.scheme,
            host=request.META["HTTP_HOST"],
            path=url + '?' + request.GET.urlencode()
        ),
    })


class PartnershipExportView(FilterMixin, PartnershipsMixinView, ExportView):
    filterset_class = PartnershipFilter

    def get_xls_headers(self):
        return [
            _('id'),
            _('partnership_type'),
            _('partnership_subtype'),
            _('continent'),
            _('country'),
            _('partner'),
            _('partner_code'),
            _('erasmus_code'),
            _('pic_code'),
            _('partner_entity'),
            _('sector'),
            _('ucl_university'),
            _('ucl_university_labo'),
            _('supervisor'),
            _('tags'),
            _('created'),
            _('modified'),
            _('end_valid_agreement'),
            _('external_id'),
        ]

    def get_xls_data(self):
        queryset = self.filterset.qs
        queryset = (
            queryset
            .annotate(
                tags_list=StringAgg('tags__value', ', '),
            )
            .select_related('author__user')
        )
        for partnership in queryset.distinct():
            last_agreement = (partnership.valid_current_agreements[0]
                              if partnership.valid_current_agreements else None)

            parts = partnership.acronym_path[1:] if partnership.acronym_path else []

            yield [
                partnership.pk,
                partnership.get_partnership_type_display(),
                str(partnership.subtype or ''),
                str(partnership.country_continent_name),
                str(partnership.country_name),
                str(partnership.partner),
                str(partnership.partner.organization.code or ''),
                str(partnership.partner.erasmus_code or ''),
                str(partnership.partner.pic_code or ''),
                str(partnership.partner_entity or ''),

                str(parts[0] if len(parts) > 0 else ''),
                str(parts[1] if len(parts) > 1 else ''),
                str(parts[2] if len(parts) > 2 else ''),

                str(partnership.supervisor or ''),
                partnership.tags_list,
                partnership.created.strftime('%Y-%m-%d'),
                partnership.modified.strftime('%Y-%m-%d'),

                getattr(
                    last_agreement,
                    'end_academic_year' if partnership.is_mobility else 'end_date',
                    '',
                ),

                partnership.external_id,
            ]

    def get_filename(self):
        return now().strftime('partnerships-%Y-%m-%d-%H-%M-%S')

    def get_title(self):
        return _('Partnerships')
