from dal import autocomplete
from django.contrib.auth.mixins import PermissionRequiredMixin
from django.db.models import Q

from base.models.person import Person

__all__ = [
    'PersonAutocompleteView',
]


class PersonAutocompleteView(PermissionRequiredMixin, autocomplete.Select2QuerySetView):
    login_url = 'access_denied'
    permission_required = 'partnership.can_access_partnerships'

    def get_queryset(self):
        qs = Person.objects.filter(employee=True)
        if self.q:
            qs = qs.filter(
                Q(first_name__icontains=self.q) |
                Q(middle_name__icontains=self.q) |
                Q(last_name__icontains=self.q)
            )
        return qs.distinct()

    def get_result_label(self, person):
        return '{0} - {1}'.format(person, person.email)
