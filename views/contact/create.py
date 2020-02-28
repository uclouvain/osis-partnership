from django.contrib import messages
from django.shortcuts import redirect
from django.utils.translation import gettext_lazy as _
from django.views.generic import CreateView

from .mixins import PartnershipContactFormMixin

__all__ = ['PartnershipContactCreateView']


class PartnershipContactCreateView(PartnershipContactFormMixin, CreateView):
    template_name = 'partnerships/contacts/partnership_contact_create.html'
    login_url = 'access_denied'

    def form_valid(self, form):
        contact = form.save()
        self.partnership.contacts.add(contact)
        messages.success(self.request, _("contact_creation_success"))
        return redirect(self.partnership)
