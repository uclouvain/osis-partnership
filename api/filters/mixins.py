from django_filters.fields import ModelMultipleChoiceField

from partnership.models import FundingType, PartnershipConfiguration


class FundingFilterMixin:
    field_class = ModelMultipleChoiceField

    def __init__(self, **kwargs):
        queryset = self.get_queryset
        super().__init__(to_field_name='name', queryset=queryset, **kwargs)

    def get_queryset(self, request):
        current_year = PartnershipConfiguration.get_configuration().get_current_academic_year_for_api()
        return FundingType.objects.filter(
            financing__academic_year=current_year,
        ).distinct()
