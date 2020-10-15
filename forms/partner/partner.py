from dal import autocomplete
from django import forms
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _

from base.forms.utils.datefield import DATE_FORMAT, DatePickerInput
from base.models.organization import Organization
from partnership.auth.predicates import is_linked_to_adri_entity
from partnership.models import Partner

__all__ = ['PartnerForm', 'OrganizationForm']


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
        exclude = ['medias', 'organization']
        widgets = {
            'is_valid': forms.CheckboxInput(),
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
        if not is_linked_to_adri_entity(user):
            del self.fields['is_valid']
        if self.instance.pk is not None:
            self.fields['now_known_as'].queryset = self.fields['now_known_as'].queryset.exclude(pk=self.instance.pk)
        self.fields['now_known_as'].queryset = self.fields['now_known_as'].queryset.order_by('organization__name')

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
        data = super().clean()
        if not data['pic_code'] or not data.get('is_ies', None):
            if data['is_nonprofit'] is None:
                self.add_error('is_nonprofit', ValidationError(_('required')))
            if data['is_public'] is None:
                self.add_error('is_public', ValidationError(_('required')))
            if not data['email']:
                self.add_error('email', ValidationError(_('required')))
            if not data['phone']:
                self.add_error('phone', ValidationError(_('required')))
            if not data['contact_type']:
                self.add_error('contact_type', ValidationError(_('required')))
        return data


class OrganizationForm(forms.ModelForm):
    start_date = forms.DateField(
        label=_('partner_start_date'),
        help_text=_('partner_start_date_help_text'),
        widget=DatePickerInput(
            format=DATE_FORMAT,
            attrs={'class': 'datepicker', 'autocomplete': 'off'},
        )
    )
    end_date = forms.DateField(
        label=_('partner_end_date'),
        required=False,
        widget=DatePickerInput(
            format=DATE_FORMAT,
            attrs={'class': 'datepicker', 'autocomplete': 'off'},
        )
    )
    website = forms.URLField(label=_('website'))

    class Meta:
        model = Organization
        fields = ['name', 'code', 'type']

    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user')
        super().__init__(*args, **kwargs)
        self.fields['name'].label = _('partner_name')
        self.fields['type'].label = _('partner_type')
        self.fields['type'].required = True
        self.fields['code'].label = _('partner_code')

        if not self.instance.pk:
            self.fields['start_date'].help_text = ''
        else:
            self.fields['start_date'].initial = self.instance.start_date
            self.fields['end_date'].initial = self.instance.end_date
            self.fields['website'].initial = self.instance.website
        if not is_linked_to_adri_entity(user):
            del self.fields['code']

    def clean(self):
        super().clean()
        data = self.cleaned_data
        if data['end_date'] and data['start_date'] > data['end_date']:
            self.add_error(
                'start_date',
                ValidationError(_('start_date_gt_end_date_error')),
            )
        return data
