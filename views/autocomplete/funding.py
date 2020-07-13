from itertools import chain

from dal.views import ViewMixin
from django.db.models import Value, F
from django.db.models.functions import Concat
from django.http import JsonResponse
from django.views import View

from osis_role.contrib.views import PermissionRequiredMixin
from partnership.models import FundingSource, FundingProgram, FundingType

__all__ = ['FundingAutocompleteView']


class FundingAutocompleteView(PermissionRequiredMixin, ViewMixin, View):
    """
    Autocomplete for fundings on PartnershipYear form
    """
    login_url = 'access_denied'
    permission_required = 'partnership.can_access_partnerships'

    def get_list(self):
        qs_source = FundingSource.objects.annotate(
            value=Concat(Value('fundingsource'), Value('-'), 'pk'),
            text=F('name'),
        ).values('value', 'text')
        if self.q:
            qs_source = qs_source.filter(text__icontains=self.q)

        qs_program = FundingProgram.objects.annotate(
            value=Concat(Value('fundingprogram'), Value('-'), 'pk'),
            text=Concat('source__name', Value(' > '), 'name'),
        ).values('value', 'text')
        if self.q:
            qs_program = qs_program.filter(text__icontains=self.q)

        qs_type = FundingType.objects.annotate(
            value=Concat(Value('fundingtype'), Value('-'), 'pk'),
            text=Concat(
                'program__source__name',
                Value(' > '),
                'program__name',
                Value(' > '),
                'name'
            ),
        ).values('value', 'text')
        if self.q:
            qs_type = qs_type.filter(text__icontains=self.q)

        return chain(qs_source, qs_program, qs_type)

    def get(self, request, *args, **kwargs):
        """Return option list json response."""
        results = self.get_list()
        return JsonResponse({
            'results': self.results(results)
        }, content_type='application/json')

    def results(self, results):
        """Return the result dictionary."""
        return [dict(id=x['value'], text=x['text'])
                for x in sorted(results, key=lambda x: x['text'])]
