from dal import autocomplete
from django.contrib.auth.mixins import PermissionRequiredMixin
from django.db.models import Q, OuterRef, Subquery

from base.models.education_group_year import EducationGroupYear
from partnership.models import PartnershipConfiguration


class UniversityOffersAutocompleteFilterView(PermissionRequiredMixin, autocomplete.Select2QuerySetView):
    login_url = 'access_denied'
    permission_required = 'partnership.can_access_partnerships'

    def get_queryset(self):
        qs = EducationGroupYear.objects.all().select_related('academic_year')

        ucl_entity = self.forwarded.get('ucl_entity', None)
        education_level = self.forwarded.get('education_level', None)
        entity = self.forwarded.get('years_entity', None)
        if self.q:
            qs = qs.filter(Q(title__icontains=self.q) | Q(acronym__icontains=self.q))
        if entity:
            qs = qs.filter(partnerships__entities=entity)
        elif education_level:
            qs = qs.filter(education_group_type__partnership_education_levels=education_level)
        elif ucl_entity:
            qs = qs.filter(partnerships__partnership__ucl_entity=ucl_entity)
        return qs.order_by('acronym').distinct('acronym')

    def get_result_label(self, result):
        return '{0.acronym} - {0.title}'.format(result)
