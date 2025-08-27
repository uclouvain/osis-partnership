from django.contrib.postgres.aggregates import StringAgg
from django.db import models
from django.db.models.expressions import (
    F, OuterRef, Subquery, Value,
)
from django.db.models.functions import Concat, Now, Right, Cast
from django.db.models.query import Prefetch
from django.http import JsonResponse
from django.urls import reverse
from django.utils.timezone import now
from django.utils.translation import gettext_lazy as _, pgettext_lazy
from django.views import View
from django_filters.rest_framework import DjangoFilterBackend
from django_filters.views import FilterMixin
from drf_spectacular.utils import extend_schema_view, extend_schema, OpenApiResponse
from rest_framework import generics
from rest_framework.permissions import AllowAny
from rest_framework.views import APIView

from base.models.academic_year import AcademicYear
from osis_common.document.xls_build import CONTENT_TYPE_XLS
from partnership.models import (
    EntityProxy,
    AgreementStatus,
    Financing,
    Media,
    Partner,
    Partnership,
    PartnershipAgreement,
    PartnershipConfiguration,
    PartnershipYear,
    PartnershipPartnerRelation,
)
from ..filters import PartnershipPartnerRelationFilter
from ..serializers import PartnershipPartnerRelationSerializer
from ...views import ExportView

__all__ = [
    'PartnershipsApiRetrieveView',
    'PartnershipsApiListView',
    'PartnershipsApiExportView',
    'partnership_get_export_url',
]


class PartnershipsApiViewMixin:
    serializer_class = PartnershipPartnerRelationSerializer
    permission_classes = (AllowAny,)

    def get_serializer_context(self):
        return {
            **super().get_serializer_context(),
            'request': self.request
        }

    def get_queryset(self):
        config = PartnershipConfiguration.get_configuration()
        academic_year = config.get_current_academic_year_for_api()
        self.academic_year = academic_year
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
            PartnershipPartnerRelation.objects
            .filter_for_api(academic_year)
            .annotate_partner_address(
                'country__continent__name',
                'country__iso_code',
                'country__name',
                'country_id',
                'city',
                'location',
            )
            .select_related(
                'entity__partnerentity',
                'entity__organization',
            ).prefetch_related(
                Prefetch(
                    'partnership',
                    queryset=Partnership.objects.add_acronyms().select_related(
                        'subtype',
                        'supervisor',
                    ).prefetch_related(
                        'contacts',
                        'missions',
                        Prefetch(
                            'partner_entities',
                            queryset=EntityProxy.objects.with_partner_info(),
                        )
                    )
                ),
                Prefetch(
                    'partnership__medias',
                    queryset=Media.objects.select_related('type').filter(
                        is_visible_in_portal=True
                    ),
                ),
                Prefetch(
                    'entity__organization__partner',
                    queryset=(
                        Partner.objects
                        .annotate_address(
                            'country__iso_code',
                            'country__name',
                            'city',
                        )
                        .annotate_website()
                        .select_related('organization')
                        .prefetch_related(
                            Prefetch(
                                'medias',
                                queryset=Media.objects.filter(
                                    is_visible_in_portal=True
                                ).select_related('type')
                            ),
                        )
                        .annotate_partnerships_count()
                    ),
                    to_attr='partner_prefetched',
                ),
                Prefetch(
                    'partnership__ucl_entity',
                    queryset=EntityProxy.objects
                    .select_related(
                        'uclmanagement_entity__academic_responsible',
                        'uclmanagement_entity__administrative_responsible',
                        'uclmanagement_entity__contact_out_person',
                        'uclmanagement_entity__contact_in_person',
                    )
                    .with_title()
                    .with_acronym()
                ),
                Prefetch(
                    'partnership__years',
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
                                queryset=EntityProxy.objects
                                .with_title()
                                .with_acronym()
                            ),
                            'education_fields',
                            'education_levels',
                            'offers',
                        ).filter(academic_year=academic_year)
                    ),
                    to_attr='current_year_for_api',
                ),
                Prefetch(
                    'partnership__agreements',
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
                        partnership_agreements_end__partnership=OuterRef('partnership_id'),
                        partnership_agreements_end__status=AgreementStatus.VALIDATED.name
                    )
                    .order_by('-end_date')
                    .values('year')[:1]
                ),
                start_year=Subquery(
                    PartnershipYear.objects.filter(
                        partnership=OuterRef('partnership_id'),
                    ).annotate(
                        name=academic_year_repr
                    ).order_by('academic_year').values('name')[:1]
                ),
                end_year=Subquery(
                    PartnershipYear.objects.filter(
                        partnership=OuterRef('partnership_id'),
                    ).annotate(
                        name=academic_year_repr
                    ).order_by('-academic_year').values('name')[:1]
                ),
                agreement_end=Subquery(
                    PartnershipAgreement.objects.filter(
                        partnership=OuterRef('partnership_id'),
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
            .distinct('pk')
            .order_by('pk')
        )


class PartnershipsApiListView(PartnershipsApiViewMixin, generics.ListAPIView):
    filter_backends = [DjangoFilterBackend]
    filterset_class = PartnershipPartnerRelationFilter


class PartnershipsApiRetrieveView(PartnershipsApiViewMixin, generics.RetrieveAPIView):
    lookup_field = 'partnership__uuid'
    lookup_url_kwarg = 'uuid'


def partnership_get_export_url(request):  # pragma: no cover
    # TODO: Fix when authentication is done in ESB (use already X-Forwarded-Host) / Shibb
    url = reverse('partnership_api_v1:export')
    return JsonResponse({
        'url': '{scheme}://{host}{path}'.format(
            scheme=request.scheme,
            host=request.headers["host"],
            path=url + '?' + request.GET.urlencode()
        ),
    })


@extend_schema_view(get=extend_schema(
    responses=OpenApiResponse(
        description='A xls file with partnerships',
        response={
            CONTENT_TYPE_XLS: {
                'schema': {
                    "type": "string",
                    "format": "binary",
                }
            }
        },
    ),
))
class PartnershipsApiExportView(FilterMixin, PartnershipsApiViewMixin, ExportView, APIView):
    filter_backends = [DjangoFilterBackend]
    filterset_class = PartnershipPartnerRelationFilter

    schema_include_filters = True
    schema_ignore_renderers_for_response = True

    def dispatch(self, request, *args, **kwargs):
        """ Ensure we do not call GenericAPIView.dispatch """
        return View.dispatch(self, request, *args, **kwargs)

    def get_xls_headers(self):
        return [
            _('id'),
            _('partnership_type'),
            _('partnership_subtype'),
            _('funding_source'),
            _('funding_program'),
            _('funding_type'),
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
            pgettext_lazy('partnership', 'created'),
            _('modified'),
            _('partnership_export_start'),
            _('partnership_export_end'),
            _('end_valid_agreement'),
            _('external_id'),
        ]

    def get_xls_data(self):
        queryset = self.filterset.qs

        queryset = (
            queryset
            .annotate_financing(self.academic_year)
            .annotate(tags_list=StringAgg('partnership__tags__value', ', '))
            .prefetch_related(
                Prefetch(
                    'partnership__years',
                    queryset=PartnershipYear.objects.select_related('academic_year'),
                ),
                Prefetch(
                    'partnership__years',
                    queryset=PartnershipYear.objects.select_related('academic_year').reverse(),
                    to_attr='reverse_years',
                ),
                'entity__entityversion_set',
            )
        )
        for rel in queryset.distinct():
            partnership = rel.partnership
            year = (partnership.current_year_for_api[0]
                    if partnership.current_year_for_api else '')
            last_agreement = (partnership.valid_current_agreements[0]
                              if partnership.valid_current_agreements else None)

            # Replace funding values if financing is eligible for mobility and not overridden in year
            if partnership.is_mobility and year and year.eligible and rel.financing_source and not year.funding_source:
                funding_source = rel.financing_source
                funding_program = rel.financing_program
                funding_type = rel.financing_type
            else:
                funding_source = year and year.funding_source
                funding_program = year and year.funding_program
                funding_type = year and year.funding_type

            parts = partnership.acronym_path[1:] if partnership.acronym_path else []

            organization = rel.entity.organization
            yield [
                partnership.pk,
                partnership.get_partnership_type_display(),
                str(partnership.subtype or ''),
                str(funding_source or ''),
                str(funding_program or ''),
                str(funding_type or ''),
                str(rel.country_continent_name),
                str(rel.country_name),
                str(organization.name),
                str(organization.code or ''),
                str(organization.partner_prefetched.erasmus_code or ''),
                str(organization.partner_prefetched.pic_code or ''),

                hasattr(rel.entity, 'partnerentity')
                and rel.entity.partnerentity.name or '',

                str(parts[0] if len(parts) > 0 else ''),
                str(parts[1] if len(parts) > 1 else ''),
                str(parts[2] if len(parts) > 2 else ''),

                str(partnership.supervisor or ''),
                rel.tags_list,
                partnership.created.strftime('%Y-%m-%d'),
                partnership.modified.strftime('%Y-%m-%d'),

                str(partnership.years.first().academic_year)
                if partnership.is_mobility else partnership.start_date,

                str(partnership.reverse_years[0].academic_year)
                if partnership.is_mobility else partnership.end_date,

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
