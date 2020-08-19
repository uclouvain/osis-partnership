from dal.views import ViewMixin
from dal_select2.views import Select2QuerySetView
from django.db.models import F, Value
from django.db.models.functions import Concat
from django.http import JsonResponse
from django.views import View

from osis_role.contrib.views import PermissionRequiredMixin
from partnership.models import FundingProgram, FundingSource, FundingType

__all__ = [
    'FundingAutocompleteView',
    'FundingProgramAutocompleteView',
    'FundingTypeAutocompleteView',
]


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


class FundingProgramAutocompleteView(PermissionRequiredMixin,
                                     Select2QuerySetView):
    login_url = 'access_denied'
    permission_required = 'partnership.can_access_partnerships'
    model = FundingProgram

    def get_queryset(self):
        qs = super().get_queryset()
        source = self.forwarded.get('funding_source', None)
        if source:
            return qs.filter(source_id=source)
        return qs.none()


class FundingTypeAutocompleteView(PermissionRequiredMixin,
                                  Select2QuerySetView):
    login_url = 'access_denied'
    permission_required = 'partnership.can_access_partnerships'
    model = FundingType

    def get_queryset(self):
        qs = super().get_queryset()
        program = self.forwarded.get('funding_program', None)
        if program:
            return qs.filter(program_id=program)
        return qs.none()
