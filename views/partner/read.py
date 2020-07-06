from django.contrib.auth.mixins import PermissionRequiredMixin
from django.db.models import Prefetch
from django.views.generic import DetailView

from partnership.models import Media, Partner, PartnerEntity

__all__ = [
    'PartnerDetailView',
]


class PartnerDetailView(PermissionRequiredMixin, DetailView):
    template_name = 'partnerships/partners/partner_detail.html'
    context_object_name = 'partner'
    login_url = 'access_denied'
    permission_required = 'partnership.can_access_partnerships'

    def get_queryset(self):
        return (
            Partner.objects
            .select_related('organization', 'author__user')
            .annotate_dates()
            .annotate_website()
            .prefetch_related(
                'tags',
                Prefetch(
                    'medias',
                    queryset=Media.objects.select_related('type'),
                ),
            )
        )

    def get_context_data(self, **kwargs):
        kwargs['entities'] = PartnerEntity.objects.filter(
            entity_version__parent__organization__partner=self.object,
        ).select_related(
            'contact_in', 'contact_out', 'entity_version', 'author__user',
        )
        return super().get_context_data(**kwargs)
