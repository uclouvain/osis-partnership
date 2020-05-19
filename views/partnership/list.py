from django.contrib.auth.mixins import PermissionRequiredMixin
from django.db.models import OuterRef, Subquery
from django.http import HttpResponseRedirect
from django.urls import reverse
from django.utils.translation import gettext_lazy as _
from django_filters.views import FilterView

from base.models.academic_year import AcademicYear
from base.utils.search import SearchMixin
from partnership.api.serializers import PartnershipAdminSerializer
from partnership.auth.predicates import (
    is_faculty_manager,
    is_linked_to_adri_entity,
)
from partnership.filter import PartnershipAdminFilter
from partnership.models import AgreementStatus, Partnership, PartnershipType

__all__ = [
    'PartnershipsListView',
]


class PartnershipsListView(PermissionRequiredMixin, SearchMixin, FilterView):
    template_name = 'partnerships/partnership/partnership_list.html'
    context_object_name = 'partnerships'
    login_url = 'access_denied'
    permission_required = 'partnership.can_access_partnerships'
    serializer_class = PartnershipAdminSerializer
    filterset_class = PartnershipAdminFilter
    cache_search = False

    def get(self, *args, **kwargs):
        if not self.request.GET and is_faculty_manager(self.request.user):
            # FIXME is it to enforce ucl_entity? Should be done in search form
            university = self.request.user.person.partnershipentitymanager_set.first().entity
            if Partnership.objects.filter(ucl_entity=university).exists():
                return HttpResponseRedirect(
                    '?ucl_entity={0}'.format(university.pk)
                )
        return super().get(*args, **kwargs)

    def get_queryset(self):
        validity_end_year = Subquery(AcademicYear.objects.filter(
            partnership_agreements_end__partnership=OuterRef('pk'),
            partnership_agreements_end__status=AgreementStatus.VALIDATED.name,
        ).order_by('-end_date').values('year')[:1])

        return (
            Partnership.objects
            .add_acronyms()
            .select_related(
                'ucl_entity',
                'partner__contact_address__country', 'partner_entity',
                'supervisor',
            )
            .annotate(
                validity_end_year=validity_end_year,
            )
        ).distinct()

    def get_context_data(self, **kwargs):
        user = self.request.user
        context = super().get_context_data(**kwargs)
        context['can_change_configuration'] = is_linked_to_adri_entity(user)
        context['can_add_partnership'] = any([
            t for t in PartnershipType
            if user.has_perm('partnership.add_partnership', t)]
        )
        context['url'] = reverse('partnerships:list')
        context['export_url'] = reverse('partnerships:export')
        context['search_button_label'] = _('search_partnership')
        return context

    def get_paginate_by(self, queryset):
        return 20
