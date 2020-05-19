from django.contrib import messages
from django.db import transaction
from django.shortcuts import redirect
from django.utils.translation import gettext_lazy as _
from django.views.generic import UpdateView

from partnership.models import PartnershipAgreement
from .mixins import PartnershipAgreementsFormMixin

__all__ = ['PartnershipAgreementUpdateView']


class PartnershipAgreementUpdateView(PartnershipAgreementsFormMixin, UpdateView):
    template_name = 'partnerships/agreements/update.html'
    login_url = 'access_denied'

    def get_queryset(self):
        return PartnershipAgreement.objects.select_related(
            'start_academic_year',
            'end_academic_year',
        )

    @transaction.atomic
    def form_valid(self, form, form_media):
        media = form_media.save(commit=False)
        if media.file and not hasattr(form_media.cleaned_data['file'], 'path'):
            media.file.name = self.get_filename(media.file.name)
        media.save()
        form_media.save_m2m()
        agreement = form.save()
        self.check_dates(agreement)
        messages.success(self.request, _('partnership_agreement_success'))
        return redirect(self.partnership)

    def post(self, request, *args, **kwargs):
        self.object = self.get_object()
        return super().post(request, *args, **kwargs)
