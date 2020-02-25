from django.conf import settings
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.core.mail import send_mail
from django.db import transaction
from django.db.models import Q
from django.shortcuts import redirect
from django.template.loader import render_to_string
from django.utils.translation import gettext_lazy as _
from django.views.generic import UpdateView

from base.models.academic_year import find_academic_years
from partnership.forms import PartnershipForm
from partnership.models import Partnership, PartnershipConfiguration, \
    PartnershipYear
from partnership.utils import user_is_adri
from partnership.views.partnership.mixins import PartnershipFormMixin

__all__ = [
    'PartnershipUpdateView',
]


class PartnershipUpdateView(LoginRequiredMixin, UserPassesTestMixin, PartnershipFormMixin, UpdateView):
    model = Partnership
    form_class = PartnershipForm
    template_name = "partnerships/partnership_update.html"
    login_url = 'access_denied'

    def dispatch(self, *args, **kwargs):
        self.object = self.get_object()
        return super().dispatch(*args, **kwargs)

    def test_func(self):
        return self.get_object().user_can_change(self.request.user)

    @transaction.atomic
    def form_valid(self, form, form_year):
        partnership = form.save()

        if (form_year.cleaned_data['end_academic_year'] != self.object.end_academic_year
                and not user_is_adri(self.request.user)):
            send_mail(
                'OSIS-Partenariats : {}'.format(
                    _('partnership_end_year_updated_{partner}_{faculty}').format(
                        partner=partnership.partner, faculty=partnership.ucl_university.most_recent_acronym
                    )
                ),
                render_to_string(
                    'partnerships/mails/plain_partnership_update.html',
                    context={
                        'user': self.request.user,
                        'partnership': partnership,
                    },
                    request=self.request,
                ),
                settings.DEFAULT_FROM_EMAIL,
                [PartnershipConfiguration.get_configuration().email_notification_to],
                html_message=render_to_string(
                    'partnerships/mails/partnership_update.html',
                    context={
                        'user': self.request.user,
                        'partnership': partnership,
                    },
                    request=self.request,
                ),
            )

        start_academic_year = form_year.cleaned_data.get('start_academic_year', None)
        from_year = form_year.cleaned_data.get('from_academic_year', None)
        end_year = form_year.cleaned_data.get('end_academic_year', None).year
        if from_year is None:
            from_year = start_academic_year.year
        else:
            from_year = from_year.year

        # Create missing start year if needed
        if start_academic_year is not None:
            start_year = start_academic_year.year
            first_year = partnership.years.order_by('academic_year__year').select_related('academic_year').first()
            if first_year is not None:
                first_year_education_fields = first_year.education_fields.all()
                first_year_education_levels = first_year.education_levels.all()
                first_year_entities = first_year.entities.all()
                first_year_offers = first_year.offers.all()
                academic_years = find_academic_years(start_year=start_year, end_year=first_year.academic_year.year - 1)
                for academic_year in academic_years:
                    first_year.id = None
                    first_year.academic_year = academic_year
                    first_year.save()
                    first_year.education_fields.set(first_year_education_fields)
                    first_year.education_levels.set(first_year_education_levels)
                    first_year.entities.set(first_year_entities)
                    first_year.offers.set(first_year_offers)

        # Update years
        academic_years = find_academic_years(start_year=from_year, end_year=end_year)
        for academic_year in academic_years:
            partnership_year = form_year.save(commit=False)
            try:
                partnership_year.pk = PartnershipYear.objects.get(
                    partnership=partnership, academic_year=academic_year
                ).pk
            except PartnershipYear.DoesNotExist:
                partnership_year.pk = None
                partnership_year.partnership = partnership
            partnership_year.academic_year = academic_year
            partnership_year.save()
            form_year.save_m2m()

        # Delete no longer used years
        query = Q(academic_year__year__gt=end_year)
        if start_academic_year is not None:
            query |= Q(academic_year__year__lt=start_year)
        PartnershipYear.objects.filter(partnership=partnership).filter(query).delete()

        messages.success(self.request, _('partnership_success'))
        return redirect(partnership)
