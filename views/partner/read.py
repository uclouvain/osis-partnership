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
            .select_related('partner_type', 'author')
            .prefetch_related(
                'tags',
                Prefetch('entities', queryset=PartnerEntity.objects.select_related(
                    'contact_in', 'contact_out', 'address', 'parent', 'author',
                )),
                Prefetch(
                    'medias',
                    queryset=Media.objects.select_related('type'),
                ),
            )
        )

    def get_context_data(self, **kwargs):
        context = super(PartnerDetailView, self).get_context_data(**kwargs)
        context['can_update_partner'] = self.object.user_can_change(self.request.user)
        context['can_add_entities'] = Partner.user_can_add(self.request.user)
        return context