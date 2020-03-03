from django.contrib import messages
from django.shortcuts import redirect
from django.utils.translation import gettext_lazy as _
from django.views.generic import UpdateView

from .mixins import PartnershipContactFormMixin

__all__ = ['PartnershipContactUpdateView']


class PartnershipContactUpdateView(PartnershipContactFormMixin, UpdateView):
    template_name = 'partnerships/contacts/partnership_contact_update.html'
    login_url = 'access_denied'

    def form_valid(self, form):
        form.save()
        messages.success(self.request, _("contact_update_success"))
        return redirect(self.partnership)
