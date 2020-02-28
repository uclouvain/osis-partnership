from django.contrib.auth.mixins import PermissionRequiredMixin
from django.db.models import Prefetch
from django.views.generic import DetailView

from partnership import perms
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
            .select_related('partner_type', 'author__user')
            .prefetch_related(
                'tags',
                Prefetch('entities', queryset=PartnerEntity.objects.select_related(
                    'contact_in', 'contact_out', 'address', 'parent', 'author__user',
                )),
                Prefetch(
                    'medias',
                    queryset=Media.objects.select_related('type'),
                ),
            )
        )

    def get_context_data(self, **kwargs):
        user = self.request.user
        context = super().get_context_data(**kwargs)
        context['can_update_partner'] = perms.user_can_change_partner(user, self.object)
        context['can_add_entities'] = perms.user_can_add_partner(user, self.object)
        return context
