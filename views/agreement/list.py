from django.urls import reverse
from django.utils.translation import gettext_lazy as _

from partnership.utils import user_is_adri
from ..partnership.list import PartnershipsListView
from ...api.serializers.agreement import PartnershipAgreementAdminSerializer
from ...filter import PartnershipAgreementAdminFilter

__all__ = ['PartnershipAgreementListView']


class PartnershipAgreementListView(PartnershipsListView):
    template_name = 'partnerships/agreements/agreement_list.html'
    context_object_name = 'agreements'
    permission_required = 'partnership.can_access_partnerships_agreements'
    serializer_class = PartnershipAgreementAdminSerializer
    filterset_class = PartnershipAgreementAdminFilter

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['is_agreements'] = True
        context['url'] = reverse('partnerships:agreements-list')
        context['export_url'] = reverse('partnerships:export_agreements')
        context['search_button_label'] = _('search_agreements')
        return context
