from django.db.models import OuterRef, Subquery

from base.models.entity_version import EntityVersion
from partnership.models import PartnershipAgreement
from partnership.utils import user_is_adri
from ..partnership.list import PartnershipsListView
from ...api.serializers.agreement import PartnershipAgreementAdminSerializer

__all__ = ['PartnershipAgreementListView']

from ...filter import PartnershipAgreementAdminFilter


class PartnershipAgreementListView(PartnershipsListView):
    context_object_name = 'agreements'
    serializer_class = PartnershipAgreementAdminSerializer
    filterset_class = PartnershipAgreementAdminFilter

    def has_permission(self):
        return super().has_permission() and user_is_adri(self.request.user)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['is_agreements'] = True
        context['can_search_agreements'] = True
        return context
