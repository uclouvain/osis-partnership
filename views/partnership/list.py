from django.contrib.auth.mixins import PermissionRequiredMixin
from django.db.models import OuterRef, Subquery
from django.http import HttpResponseRedirect
from django.urls import reverse
from django.utils.translation import gettext_lazy as _
from django_filters.views import FilterView

from base.models.academic_year import AcademicYear
from base.models.entity_version import EntityVersion
from base.utils.search import SearchMixin
from partnership import perms
from partnership.api.serializers import PartnershipAdminSerializer
from partnership.filter import PartnershipAdminFilter
from partnership.models import AgreementStatus, Partnership
from partnership.utils import user_is_adri, user_is_gf

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
        if not self.request.GET and user_is_gf(self.request.user):
            university = self.request.user.person.partnershipentitymanager_set.first().entity
            if Partnership.objects.filter(ucl_university=university).exists():
                return HttpResponseRedirect(
                    '?ucl_university={0}'.format(university.pk)
                )
        return super().get(*args, **kwargs)

    def get_queryset(self):
        validity_end_year = Subquery(AcademicYear.objects.filter(
            partnership_agreements_end__partnership=OuterRef('pk'),
            partnership_agreements_end__status=AgreementStatus.VALIDATED.name,
        ).order_by('-end_date').values('year')[:1])
        return (
            Partnership.objects
            .all()
            .select_related(
                'ucl_university_labo', 'ucl_university',
                'partner__contact_address__country', 'partner_entity',
                'supervisor',
            )
            .annotate(
                validity_end_year=validity_end_year,
                ucl_university_parent_most_recent_acronym=Subquery(
                    EntityVersion.objects
                    .filter(entity__parent_of__entity=OuterRef('ucl_university__pk'))
                    .order_by('-start_date')
                    .values('acronym')[:1]
                ),
                ucl_university_parent_most_recent_title=Subquery(
                    EntityVersion.objects
                    .filter(entity__parent_of__entity=OuterRef('ucl_university__pk'))
                    .order_by('-start_date')
                    .values('title')[:1]
                ),
                ucl_university_most_recent_acronym=Subquery(
                    EntityVersion.objects
                    .filter(entity=OuterRef('ucl_university__pk'))
                    .order_by('-start_date')
                    .values('acronym')[:1]
                ),
                ucl_university_most_recent_title=Subquery(
                    EntityVersion.objects
                    .filter(entity=OuterRef('ucl_university__pk'))
                    .order_by('-start_date')
                    .values('title')[:1]
                ),
                ucl_university_labo_most_recent_acronym=Subquery(
                    EntityVersion.objects
                    .filter(entity=OuterRef('ucl_university_labo__pk'))
                    .order_by('-start_date')
                    .values('acronym')[:1]
                ),
                ucl_university_labo_most_recent_title=Subquery(
                    EntityVersion.objects
                    .filter(entity=OuterRef('ucl_university_labo__pk'))
                    .order_by('-start_date')
                    .values('title')[:1]
                ),
            )
        ).distinct()

    def get_context_data(self, **kwargs):
        user = self.request.user
        context = super().get_context_data(**kwargs)
        context['can_change_configuration'] = user_is_adri(user)
        context['can_add_partnership'] = perms.user_can_add_partnership(user)
        context['url'] = reverse('partnerships:list')
        context['export_url'] = reverse('partnerships:export')
        context['search_button_label'] = _('search_partnership')
        return context

    def get_paginate_by(self, queryset):
        return 20
