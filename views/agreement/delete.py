from django.views.generic import DeleteView

from partnership import perms
from .mixins import PartnershipAgreementsMixin

__all__ = ['PartnershipAgreementDeleteView']


class PartnershipAgreementDeleteView(PartnershipAgreementsMixin, DeleteView):
    template_name = 'partnerships/agreements/delete.html'
    login_url = 'access_denied'

    def test_func(self):
        return perms.user_can_delete_agreement(self.request.user, self.get_object())

    def get_template_names(self):
        if self.request.is_ajax():
            return 'partnerships/agreements/includes/delete.html'
        return self.template_name
