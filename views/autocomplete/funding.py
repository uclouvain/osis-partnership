from dal.views import ViewMixin
from django.db.models import F, Value
from django.db.models.functions import Concat
from django.http import JsonResponse
from django.views import View

from osis_role.contrib.views import PermissionRequiredMixin
from partnership.models import FundingProgram, FundingSource, FundingType

__all__ = ['FundingAutocompleteView']


class FundingAutocompleteView(PermissionRequiredMixin, ViewMixin, View):
    """
    Autocomplete for fundings on PartnershipYear form
    """
    login_url = 'access_denied'
    permission_required = 'partnership.can_access_partnerships'

    def get_list(self):
        return FundingSource.objects.annotate(
            value=Concat(Value('fundingsource'), Value('-'), 'pk'),
            text=F('name'),
        ).filter(text__icontains=self.q).values('value', 'text').union(
            FundingProgram.objects.annotate(
                value=Concat(Value('fundingprogram'), Value('-'), 'pk'),
                text=Concat('source__name', Value(' > '), 'name'),
            ).filter(text__icontains=self.q).values('value', 'text')
        ).union(
            FundingType.objects.annotate(
                value=Concat(Value('fundingtype'), Value('-'), 'pk'),
                text=Concat(
                    'program__source__name',
                    Value(' > '),
                    'program__name',
                    Value(' > '),
                    'name'
                ),
            ).filter(text__icontains=self.q).values('value', 'text')
        ).order_by('text')

    def get(self, request, *args, **kwargs):
        """Return option list json response."""
        results = self.get_list()
        return JsonResponse({
            'results': [dict(id=x['value'], text=x['text']) for x in results]
        }, content_type='application/json')
