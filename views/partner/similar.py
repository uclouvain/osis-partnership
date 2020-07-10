from django.contrib.auth.mixins import PermissionRequiredMixin
from django.views.generic import ListView

from partnership.models import Partner


class SimilarPartnerView(PermissionRequiredMixin, ListView):
    template_name = 'partnerships/partners/includes/similar_partners_preview.html'
    context_object_name = 'similar_partners'
    login_url = 'access_denied'
    permission_required = 'partnership.can_access_partnerships'

    def get_queryset(self):
        search = self.request.GET.get('search', '')
        # Don't query for small searches
        if len(search) < 3:
            return Partner.objects.none()
        return Partner.objects.filter(organization__name__icontains=search)[:10]
