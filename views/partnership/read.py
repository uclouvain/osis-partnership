from django.conf import settings
from django.contrib.auth.mixins import PermissionRequiredMixin
from django.db.models import Prefetch
from django.shortcuts import get_object_or_404
from django.utils.translation import get_language
from django.views.generic import DetailView

from base.models.organization import Organization
from partnership.models import (
    Media, Partnership, PartnershipAgreement, PartnershipType, PartnershipYear,
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
        context['domain_title'] = (
            'title_fr' if get_language() == settings.LANGUAGE_CODE_FR
            else 'title_en'
        )

        if self.object.partnership_type not in PartnershipType.with_synced_dates():
            context['show_more_year_link'] = False
        elif self.object.current_year is None:
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
                'ucl_entity',
                'author__user',
                'supervisor',
                'partner_referent',
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
                Prefetch(
                    'partner_entities__organization',
                    queryset=Organization.objects.order_by('name').select_related('partner')
                ),
                Prefetch(
                    'partner_referent__organization',
                    queryset=Organization.objects.order_by('name').select_related('partner')
                ),
                # Prefetch(
                #     'partnershiprelation',
                #     queryset=Organization.objects.order_by('name').select_related('partner')
                # ),

            ),
            pk=self.kwargs['pk'],
        )
