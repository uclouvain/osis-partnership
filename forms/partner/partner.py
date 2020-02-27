from dal import autocomplete
from django import forms
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _

from base.forms.utils.datefield import DATE_FORMAT, DatePickerInput
from partnership.models import Partner
from partnership.utils import user_is_adri

__all__ = ['PartnerForm']


class PartnerForm(forms.ModelForm):
    is_ies = forms.ChoiceField(
        label=_('is_ies'),
        initial=None,
        required=True,
        choices=(
            (None, '---------'),
            (True, _('Yes')),
            (False, _('No')),
        ),
    )

    is_nonprofit = forms.ChoiceField(
        label=_('is_nonprofit'),
        help_text=_('mandatory_if_not_pic_ies'),
        required=False,
        choices=(
            (None, '---------'),
            (True, _('Yes')),
            (False, _('No')),
        ),
    )

    is_public = forms.ChoiceField(
        label=_('is_public'),
        help_text=_('mandatory_if_not_pic_ies'),
        required=False,
        choices=(
            (None, '---------'),
            (True, _('Yes')),
            (False, _('No')),
        ),
    )

    class Meta:
        model = Partner
        exclude = ['external_id', 'contact_address', 'medias']
        widgets = {
            'name': forms.TextInput(attrs={'placeholder': _('partner_name')}),
            'is_valid': forms.CheckboxInput(),
            'start_date': DatePickerInput(
                format=DATE_FORMAT,
                attrs={'class': 'datepicker', 'placeholder': _('partner_start_date'), 'autocomplete': 'off'},
            ),
            'end_date': DatePickerInput(
                format=DATE_FORMAT,
                attrs={'class': 'datepicker', 'placeholder': _('partner_end_date'), 'autocomplete': 'off'},
            ),
            'partner_code': forms.TextInput(attrs={'placeholder': _('partner_code')}),
            'pic_code': forms.TextInput(attrs={'placeholder': _('pic_code')}),
            'erasmus_code': forms.TextInput(attrs={'placeholder': _('erasmus_code')}),
            'use_egracons': forms.CheckboxInput(),
            'comment': forms.Textarea(attrs={'placeholder': _('comment')}),
            'phone': forms.TextInput(attrs={'placeholder': _('phone')}),
            'website': forms.URLInput(attrs={'placeholder': _('website')}),
            'email': forms.EmailInput(attrs={'placeholder': _('email')}),
            'tags': autocomplete.ModelSelect2Multiple(),
            'now_known_as': autocomplete.ModelSelect2(),
        }

    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user')
        super().__init__(*args, **kwargs)
        if not user_is_adri(user):
            del self.fields['is_valid']
            del self.fields['partner_code']
        if self.instance.pk is not None:
            self.fields['now_known_as'].queryset = self.fields['now_known_as'].queryset.exclude(pk=self.instance.pk)
        self.fields['now_known_as'].queryset = self.fields['now_known_as'].queryset.order_by('name')

    def _clean_choice_boolean(self, value):
        values = {
            '': None,
            'True': True,
            'False': False,
        }
        return values.get(value, value)

    def clean_is_ies(self):
        return self._clean_choice_boolean(self.cleaned_data.get('is_ies', None))

    def clean_is_nonprofit(self):
        return self._clean_choice_boolean(self.cleaned_data.get('is_nonprofit', None))

    def clean_is_public(self):
        return self._clean_choice_boolean(self.cleaned_data.get('is_public', None))

    def clean(self):
        super().clean()
        if self.cleaned_data['start_date'] and self.cleaned_data['end_date']:
            if self.cleaned_data['start_date'] > self.cleaned_data['end_date']:
                self.add_error('start_date', ValidationError(_('start_date_gt_end_date_error')))
        if not self.cleaned_data['pic_code'] or not self.cleaned_data.get('is_ies', None):
            if self.cleaned_data['is_nonprofit'] is None:
                self.add_error('is_nonprofit', ValidationError(_('required')))
            if self.cleaned_data['is_public'] is None:
                self.add_error('is_public', ValidationError(_('required')))
            if not self.cleaned_data['email']:
                self.add_error('email', ValidationError(_('required')))
            if not self.cleaned_data['phone']:
                self.add_error('phone', ValidationError(_('required')))
            if not self.cleaned_data['contact_type']:
                self.add_error('contact_type', ValidationError(_('required')))

        return self.cleaned_data