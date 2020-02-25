from dal import autocomplete
from django.contrib.auth.mixins import PermissionRequiredMixin

from base.models.education_group_year import EducationGroupYear
from partnership.models import PartnershipConfiguration


class UniversityOffersAutocompleteFilterView(PermissionRequiredMixin, autocomplete.Select2QuerySetView):
    login_url = 'access_denied'
    permission_required = 'partnership.can_access_partnerships'

    def get_queryset(self):
        qs = EducationGroupYear.objects.all().select_related('academic_year')
        next_academic_year = \
            PartnershipConfiguration.get_configuration().get_current_academic_year_for_creation_modification()
        qs = qs.filter(academic_year=next_academic_year)
        ucl_university = self.forwarded.get('ucl_university', None)
        education_level = self.forwarded.get('education_level', None)
        entity = self.forwarded.get('years_entity', None)
        if not ucl_university or not education_level:
            return EducationGroupYear.objects.none()
        if entity:
            qs = qs.filter(partnerships__entities=entity)
        else:
            qs = qs.filter(partnerships__partnership__ucl_university=ucl_university)
        qs = qs.filter(education_group_type__partnership_education_levels=education_level)
        if self.q:
            qs = qs.filter(title__icontains=self.q)
        return qs.distinct()

    def get_result_label(self, result):
        return '{0.acronym} - {0.title}'.format(result)
