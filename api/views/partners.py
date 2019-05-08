from django.db import models
from django.db.models import Value, Count, Exists, OuterRef, Subquery
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import generics
from rest_framework.permissions import AllowAny

from partnership.api.filters import PartnerFilter
from partnership.api.serializers import PartnerSerializer
from partnership.models import PartnershipConfiguration, Partner, \
    PartnershipAgreement, PartnershipYearEducationField


class PartnersListView(generics.ListAPIView):
    serializer_class = PartnerSerializer
    permission_classes = (AllowAny,)
    filter_backends = [DjangoFilterBackend]
    filterset_class = PartnerFilter

    def get_queryset(self):
        academic_year = PartnershipConfiguration.get_configuration().get_current_academic_year_for_api()

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
            )
            .filter(has_in=True)
            .distinct()
        )

    def filter_queryset(self, queryset):
        return super().filter_queryset(queryset).annotate(
            # This needs to be after all the filtering done on partnerships
            partnerships_count=Count('partnerships', distinct=True),
        )
