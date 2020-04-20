from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.db import transaction
from django.shortcuts import redirect
from django.utils.translation import gettext_lazy as _
from django.views.generic import CreateView

from base.models.academic_year import find_academic_years
from partnership import perms
from partnership.forms import PartnershipForm
from partnership.models import Partnership
from partnership.utils import user_is_adri
from partnership.views.mixins import NotifyAdminMailMixin
from partnership.views.partnership.mixins import PartnershipFormMixin

__all__ = [
    'PartnershipCreateView',
]


class PartnershipCreateView(LoginRequiredMixin,
                            UserPassesTestMixin,
                            NotifyAdminMailMixin,
                            PartnershipFormMixin,
                            CreateView):
    model = Partnership
    form_class = PartnershipForm
    template_name = "partnerships/partnership/partnership_create.html"
    login_url = 'access_denied'

    def test_func(self):
        return perms.user_can_add_partnership(self.request.user)

    @transaction.atomic
    def form_valid(self, form, form_year):
        partnership = form.save(commit=False)
        partnership.author = self.request.user.person

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
            title = '{} - {}'.format(
                _('partnership_created'),
                partnership.ucl_university.most_recent_acronym
            )
            self.notify_admin_mail(title, 'partnership_creation.html', {
                'partnership': partnership,
            })
        return redirect(partnership)

    def post(self, request, *args, **kwargs):
        self.object = None
        return super().post(request, *args, **kwargs)
