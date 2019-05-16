from django.db import models
from django.db.models import Value, Count, Exists, OuterRef, Subquery, F
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import generics
from rest_framework.permissions import AllowAny

from partnership.api.filters import PartnerFilter, PartnershipFilter
from partnership.api.serializers import PartnerSerializer
from partnership.models import PartnershipConfiguration, Partner, \
    PartnershipAgreement, PartnershipYearEducationField, Partnership


class PartnersListView(generics.ListAPIView):
    serializer_class = PartnerSerializer
    permission_classes = (AllowAny,)
    filter_backends = [DjangoFilterBackend]
    filterset_class = PartnerFilter

    def get_partnerships_count_subquery(self, academic_year):
        # Partnership queryset for subquery count
        partnerships_queryset = Partnership.objects.annotate(
            current_academic_year=Value(academic_year.id, output_field=models.AutoField()),
            has_in=Exists(
                PartnershipAgreement.objects.filter(
                    partnership=OuterRef('pk'),
                    start_academic_year__year__lte=academic_year.year,
                    end_academic_year__year__gte=academic_year.year,
                )
            ),
        ).filter(
            has_in=True,
            years__academic_year=F('current_academic_year'),  # From annotation
        )
        partnerships_filter = PartnershipFilter(
            data=self.request.query_params,
            queryset=partnerships_queryset,
            request=self.request,
        )
        partnerships_filter.is_valid()
        partnerships_queryset = (
            partnerships_filter.qs
                .order_by()
                .filter(partner=OuterRef('pk'))
                .annotate(count=Count('pk', distinct=True))
                .values('count')
        )
        # Django ORM add a group_by id in some requests, we need to remove it.
        # It should be done with a Count(filter=,,,) in Django >= 2.0 instead of a subquery
        partnerships_queryset.query.group_by = None
        return partnerships_queryset

    def get_queryset(self):
        academic_year = PartnershipConfiguration.get_configuration().get_current_academic_year_for_api()
        partnerships_queryset = self.get_partnerships_count_subquery(academic_year)

        return (
            Partner.objects
            .select_related('partner_type', 'contact_address__country')
            .annotate(
                current_academic_year=Value(academic_year.id, output_field=models.AutoField()),
                has_in=Exists(
                    PartnershipAgreement.objects.filter(
                        partnership__partner=OuterRef('pk'),
                        start_academic_year__year__lte=academic_year.year,
                        end_academic_year__year__gte=academic_year.year,
                    )
                ),
                subject_area_ordered=Subquery(  # For ordering only
                    PartnershipYearEducationField.objects
                    .filter(
                        partnershipyear__academic_year=academic_year,
                        partnershipyear__partnership__partner=OuterRef('pk'),
                    )
                    .order_by('label')
                    .values('label')[:1]
                ),
                partnerships_count=Subquery(
                    partnerships_queryset,
                    output_field=models.IntegerField()
                ),
            )
            .exclude(partnerships_count=0)
            .filter(
                has_in=True,
                partnerships__years__academic_year=academic_year,  # From annotation
            )
            .distinct()
        )
