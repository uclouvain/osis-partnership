from django.contrib.auth.mixins import PermissionRequiredMixin
from django.db.models import Prefetch
from django.shortcuts import get_object_or_404
from django.views.generic import DetailView

from partnership.models import (
    Media, Partnership, PartnershipAgreement, PartnershipYear,
)

__all__ = [
    'PartnershipDetailView',
]


class PartnershipDetailView(PermissionRequiredMixin, DetailView):
    model = Partnership
    context_object_name = 'partnership'
    login_url = 'access_denied'
    permission_required = 'partnership.can_access_partnerships'

    def get_template_names(self):
        return [
            'partnerships/partnership/partnership_detail_{}.html'.format(
                self.object.partnership_type.lower()
            ),
            'partnerships/partnership/partnership_detail.html',
        ]

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
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
            .add_acronyms()
            .select_related(
                'partner', 'partner_entity', 'ucl_entity', 'author__user',
                'supervisor',
                'ucl_entity__uclmanagement_entity__academic_responsible',
                'ucl_entity__uclmanagement_entity__contact_in_person',
                'ucl_entity__uclmanagement_entity__contact_out_person',
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
