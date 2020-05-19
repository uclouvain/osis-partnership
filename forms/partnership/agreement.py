from django import forms
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _

from partnership.auth.predicates import is_linked_to_adri_entity
from partnership.models import PartnershipAgreement

__all__ = ['PartnershipAgreementForm']


class PartnershipAgreementForm(forms.ModelForm):

    class Meta:
        model = PartnershipAgreement
        fields = [
            'start_academic_year',
            'end_academic_year',
            'status',
            'comment',
        ]

    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user')
        super().__init__(*args, **kwargs)
        if not is_linked_to_adri_entity(user):
            del self.fields['status']

    def clean(self):
        super().clean()
        start_academic_year = self.cleaned_data.get('start_academic_year', None)
        end_academic_year = self.cleaned_data.get('end_academic_year', None)
        if (start_academic_year is not None and end_academic_year is not None
                and start_academic_year.year > end_academic_year.year):
            self.add_error('start_academic_year', ValidationError(_('start_date_after_end_date')))
            self.add_error('end_academic_year', ValidationError(_('start_date_after_end_date')))
        return self.cleaned_data
