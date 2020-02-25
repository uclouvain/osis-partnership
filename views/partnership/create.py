from django.conf import settings
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.core.mail import send_mail
from django.db import transaction
from django.shortcuts import redirect
from django.template.loader import render_to_string
from django.utils.translation import gettext_lazy as _
from django.views.generic import CreateView

from base.models.academic_year import find_academic_years
from partnership.forms import PartnershipForm
from partnership.models import Partnership, PartnershipConfiguration
from partnership.utils import user_is_adri
from partnership.views.partnership.mixins import PartnershipFormMixin

__all__ = [
    'PartnershipCreateView',
]


class PartnershipCreateView(LoginRequiredMixin, UserPassesTestMixin, PartnershipFormMixin, CreateView):
    model = Partnership
    form_class = PartnershipForm
    template_name = "partnerships/partnership_create.html"
    login_url = 'access_denied'

    def test_func(self):
        return Partnership.user_can_add(self.request.user)

    @transaction.atomic
    def form_valid(self, form, form_year):
        partnership = form.save(commit=False)
        partnership.author = self.request.user

        # Resume saving
        partnership.save()
        form.save_m2m()

        # Create years
        start_year = form_year.cleaned_data['start_academic_year'].year
        end_year = form_year.cleaned_data['end_academic_year'].year
        academic_years = find_academic_years(start_year=start_year, end_year=end_year)
        for academic_year in academic_years:
            partnership_year = form_year.save(commit=False)
            partnership_year.id = None  # Force the creation of a new PartnershipYear
            partnership_year.partnership = partnership
            partnership_year.academic_year = academic_year
            partnership_year.save()
            form_year.save_m2m()

        messages.success(self.request, _('partnership_success'))
        if not user_is_adri(self.request.user):
            send_mail(
                'OSIS-Partenariats : {} - {}'.format(
                    _('partnership_created'),
                    partnership.ucl_university.most_recent_acronym
                ),
                render_to_string(
                    'partnerships/mails/plain_partnership_creation.html',
                    context={
                        'user': self.request.user,
                        'partnership': partnership,
                    },
                    request=self.request,
                ),
                settings.DEFAULT_FROM_EMAIL,
                [PartnershipConfiguration.get_configuration().email_notification_to],
                html_message=render_to_string(
                    'partnerships/mails/partnership_creation.html',
                    context={
                        'user': self.request.user,
                        'partnership': partnership,
                    },
                    request=self.request,
                ),
            )
        return redirect(partnership)

    def post(self, request, *args, **kwargs):
        self.object = None
        return super().post(request, *args, **kwargs)
