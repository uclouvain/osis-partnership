from django.contrib import messages
from django.db import transaction
from django.shortcuts import redirect
from django.utils.translation import gettext_lazy as _
from django.views.generic import CreateView

from partnership import perms
from partnership.utils import user_is_adri
from .mixins import PartnershipAgreementsFormMixin
from ..mixins import NotifyAdminMailMixin

__all__ = ['PartnershipAgreementCreateView']


class PartnershipAgreementCreateView(NotifyAdminMailMixin,
                                     PartnershipAgreementsFormMixin,
                                     CreateView):
    template_name = 'partnerships/agreements/create.html'
    login_url = 'access_denied'

    def test_func(self):
        return perms.user_can_change_partnership(self.request.user, self.partnership)

    @transaction.atomic
    def form_valid(self, form, form_media):
        media = form_media.save(commit=False)
        media.author = self.request.user.person
        if media.file:
            media.file.name = self.get_filename(media.file.name)
        media.save()
        form_media.save_m2m()
        agreement = form.save(commit=False)
        agreement.partnership = self.partnership
        agreement.media = media
        agreement.save()
        form.save_m2m()
        self.check_dates(agreement)
        messages.success(self.request, _('partnership_agreement_success'))

        # Send notification e-mail when not ADRI
        if not user_is_adri(self.request.user):
            title = '{} - {}'.format(
                _('partnership_agreement_created'),
                self.partnership.ucl_entity.most_recent_acronym
            )
            self.notify_admin_mail(title, 'agreement_creation.html', {
                'partnership': self.partnership,
            })
        return redirect(self.partnership)

    def post(self, request, *args, **kwargs):
        self.object = None
        return super().post(request, *args, **kwargs)
