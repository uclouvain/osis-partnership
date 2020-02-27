from django.contrib.auth.mixins import PermissionRequiredMixin
from django.db.models import Prefetch
from django.shortcuts import get_object_or_404
from django.views.generic import DetailView

from partnership import perms
from partnership.models import (
    Media, Partnership, PartnershipAgreement, PartnershipYear,
)

__all__ = [
    'PartnershipDetailView',
]


class PartnershipDetailView(PermissionRequiredMixin, DetailView):
    model = Partnership
    context_object_name = 'partnership'
    template_name = 'partnerships/partnership_detail.html'
    login_url = 'access_denied'
    permission_required = 'partnership.can_access_partnerships'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['can_change'] = perms.user_can_change_partnership(
            self.request.user, self.object
        )
        if self.object.current_year is None:
            context['show_more_year_link'] = self.object.years.count() > 1
        else:
            year = self.object.current_year.academic_year.year
            context['show_more_year_link'] = self.object.years.exclude(
                academic_year__year__in=[year, year + 1]
            ).exists()
        return context

    def get_object(self, queryset=None):
        return get_object_or_404(
            Partnership.objects
            .select_related(
                'partner', 'partner_entity', 'ucl_university',
                'ucl_university_labo', 'author'
            )
            .prefetch_related(
                'contacts',
                'tags',
                Prefetch(
                    'medias',
                    queryset=Media.objects.select_related('type'),
                ),
                Prefetch(
                    'years',
                    queryset=PartnershipYear.objects.select_related('academic_year')
                ),
                Prefetch('agreements', queryset=PartnershipAgreement.objects.select_related(
                    'start_academic_year', 'end_academic_year', 'media'
                ).order_by("-start_academic_year", "-end_academic_year")),
            ),
            pk=self.kwargs['pk'],
        )
