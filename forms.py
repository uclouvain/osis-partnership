from datetime import date

from dal import autocomplete, forward
from django import forms
from django.core.exceptions import ValidationError
from django.utils.translation import ugettext_lazy as _

from base.forms.utils.datefield import DATE_FORMAT, DatePickerInput
from base.models.academic_year import AcademicYear
from base.models.education_group_year import EducationGroupYear
from base.models.entity import Entity
from base.models.person import Person
from partnership.models import (Address, Contact, Media, Partner,
                                PartnerEntity, Partnership,
                                PartnershipAgreement, PartnershipConfiguration,
                                PartnershipTag, PartnershipYear,
                                PartnershipYearEducationField,
                                PartnershipYearEducationLevel, PartnerTag,
                                PartnerType, UCLManagementEntity)
from partnership.utils import user_is_adri
from reference.models.continent import Continent
from reference.models.country import Country


class CustomNullBooleanSelect(forms.NullBooleanSelect):

    def __init__(self, attrs=None):
        choices = (
            ('1', '---------'),
            ('2', _('Yes')),
            ('3', _('No')),
        )
        super(forms.NullBooleanSelect, self).__init__(attrs, choices)


class EducationGroupYearChoiceSelect(forms.ModelMultipleChoiceField):

    def label_from_instance(self, obj):
        return '{0} - {1}'.format(obj.acronym, obj.title)


class PartnerForm(forms.ModelForm):
    class Meta:
        model = Partner
        exclude = ['contact_address', 'medias']
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
            'is_ies': forms.CheckboxInput(),
            'is_nonprofit': forms.CheckboxInput(),
            'is_public': forms.CheckboxInput(),
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
        super(PartnerForm, self).__init__(*args, **kwargs)
        if not user_is_adri(user):
            del self.fields['is_valid']
            del self.fields['partner_code']
        if self.instance.pk is not None:
            self.fields['now_known_as'].queryset = self.fields['now_known_as'].queryset.exclude(pk=self.instance.pk)
        self.fields['now_known_as'].queryset = self.fields['now_known_as'].queryset.order_by('name')

    def clean(self):
        super(PartnerForm, self).clean()
        if self.cleaned_data['start_date'] and self.cleaned_data['end_date']:
            if self.cleaned_data['start_date'] > self.cleaned_data['end_date']:
                self.add_error('start_date', ValidationError(_('start_date_gt_end_date_error')))

        if not self.cleaned_data['pic_code'] and not self.cleaned_data['is_ies']:
            if not self.cleaned_data['email']:
                self.add_error('email', ValidationError(_('required')))
            if not self.cleaned_data['phone']:
                self.add_error('phone', ValidationError(_('required')))
            if not self.cleaned_data['contact_type']:
                self.add_error('contact_type', ValidationError(_('required')))

        return self.cleaned_data


class PartnerEntityForm(forms.ModelForm):

    """
    This form include fields for related models Address and two Contact.
    """

    # Address

    address_name = forms.CharField(
        label=_('Name'),
        widget=forms.TextInput(attrs={'placeholder': _('address_name_help_text')}),
        required=False,
    )
    address_address = forms.CharField(
        label=_('address'),
        widget=forms.TextInput(attrs={'placeholder': _('address')}),
        required=False,
    )
    address_postal_code = forms.CharField(
        label=_('postal_code'),
        widget=forms.TextInput(attrs={'placeholder': _('postal_code')}),
        required=False,
    )
    address_city = forms.CharField(
        label=_('city'),
        widget=forms.TextInput(attrs={'placeholder': _('city')}),
        required=False,
    )
    address_country = forms.ModelChoiceField(
        label=_('country'),
        queryset=Country.objects.order_by('name'),
        empty_label=_('country'),
        required=False,
    )

    # Contact in

    contact_in_title = forms.ChoiceField(
        label=_('contact_title'),
        choices=((None, '---------'),) + Contact.TITLE_CHOICES,
        required=False,
    )

    contact_in_last_name = forms.CharField(
        label=_('last_name'),
        widget=forms.TextInput(attrs={'placeholder': _('last_name')}),
        required=False,
    )

    contact_in_first_name = forms.CharField(
        label=_('first_name'),
        widget=forms.TextInput(attrs={'placeholder': _('first_name')}),
        required=False,
    )

    contact_in_function = forms.CharField(
        label=_('function'),
        widget=forms.TextInput(attrs={'placeholder': _('function')}),
        required=False,
    )

    contact_in_phone = forms.CharField(
        label=_('phone'),
        widget=forms.TextInput(attrs={'placeholder': _('phone')}),
        required=False,
    )

    contact_in_mobile_phone = forms.CharField(
        label=_('mobile_phone'),
        widget=forms.TextInput(attrs={'placeholder': _('mobile_phone')}),
        required=False,
    )

    contact_in_fax = forms.CharField(
        label=_('fax'),
        widget=forms.TextInput(attrs={'placeholder': _('fax')}),
        required=False,
    )

    contact_in_email = forms.EmailField(
        label=_('email'),
        widget=forms.EmailInput(attrs={'placeholder': _('email')}),
        required=False,
    )

    # Contact out

    contact_out_title = forms.ChoiceField(
        label=_('contact_title'),
        choices=((None, '---------'),) + Contact.TITLE_CHOICES,
        required=False,
    )

    contact_out_last_name = forms.CharField(
        label=_('last_name'),
        widget=forms.TextInput(attrs={'placeholder': _('last_name')}),
        required=False,
    )

    contact_out_first_name = forms.CharField(
        label=_('first_name'),
        widget=forms.TextInput(attrs={'placeholder': _('first_name')}),
        required=False,
    )

    contact_out_function = forms.CharField(
        label=_('function'),
        widget=forms.TextInput(attrs={'placeholder': _('function')}),
        required=False,
    )

    contact_out_phone = forms.CharField(
        label=_('phone'),
        widget=forms.TextInput(attrs={'placeholder': _('phone')}),
        required=False,
    )

    contact_out_mobile_phone = forms.CharField(
        label=_('mobile_phone'),
        widget=forms.TextInput(attrs={'placeholder': _('mobile_phone')}),
        required=False,
    )

    contact_out_fax = forms.CharField(
        label=_('fax'),
        widget=forms.TextInput(attrs={'placeholder': _('fax')}),
        required=False,
    )

    contact_out_email = forms.EmailField(
        label=_('email'),
        widget=forms.EmailInput(attrs={'placeholder': _('email')}),
        required=False,
    )

    class Meta:
        model = PartnerEntity
        exclude = ('partner', 'address', 'contact_in', 'contact_out')
        widgets = {
            'name': forms.TextInput(attrs={'placeholder': _('name')}),
            'comment': forms.Textarea(attrs={'placeholder': _('comment')}),
        }

    def __init__(self, *args, **kwargs):
        partner = kwargs.pop('partner')
        super(PartnerEntityForm, self).__init__(*args, **kwargs)
        self.fields['parent'].queryset = PartnerEntity.objects.filter(partner=partner).exclude(pk=self.instance.pk)

    def get_initial_for_field(self, field, field_name):
        """ Set value of foreign keys fields """
        value = super(PartnerEntityForm, self).get_initial_for_field(field, field_name)
        if value is None:
            if field_name.startswith('address_'):
                value = getattr(self.instance.address, field_name[len('address_'):], None)
            elif field_name.startswith('contact_in_'):
                value = getattr(self.instance.contact_in, field_name[len('contact_in_'):], None)
            elif field_name.startswith('contact_out_'):
                value = getattr(self.instance.contact_out, field_name[len('contact_out_'):], None)
        return value

    def save_address(self, partner_entity, commit=True):
        if partner_entity.address is None:
            partner_entity.address = Address()
        address = partner_entity.address
        address.name = self.cleaned_data['address_name']
        address.address = self.cleaned_data['address_address']
        address.postal_code = self.cleaned_data['address_postal_code']
        address.city = self.cleaned_data['address_city']
        address.country = self.cleaned_data['address_country']
        if commit:
            address.save()
            partner_entity.address_id = address.id
        return address

    def save_contact_in(self, partner_entity, commit=True):
        if partner_entity.contact_in is None:
            partner_entity.contact_in = Contact()
        contact_in = partner_entity.contact_in
        contact_in.title = self.cleaned_data['contact_in_title']
        contact_in.last_name = self.cleaned_data['contact_in_last_name']
        contact_in.first_name = self.cleaned_data['contact_in_first_name']
        contact_in.function = self.cleaned_data['contact_in_function']
        contact_in.phone = self.cleaned_data['contact_in_phone']
        contact_in.mobile_phone = self.cleaned_data['contact_in_mobile_phone']
        contact_in.fax = self.cleaned_data['contact_in_fax']
        contact_in.email = self.cleaned_data['contact_in_email']
        if commit:
            contact_in.save()
            partner_entity.contact_in_id = contact_in.id
        return contact_in

    def save_contact_out(self, partner_entity, commit=True):
        if partner_entity.contact_out is None:
            partner_entity.contact_out = Contact()
        contact_out = partner_entity.contact_out
        contact_out.title = self.cleaned_data['contact_out_title']
        contact_out.last_name = self.cleaned_data['contact_out_last_name']
        contact_out.first_name = self.cleaned_data['contact_out_first_name']
        contact_out.function = self.cleaned_data['contact_out_function']
        contact_out.phone = self.cleaned_data['contact_out_phone']
        contact_out.mobile_phone = self.cleaned_data['contact_out_mobile_phone']
        contact_out.fax = self.cleaned_data['contact_out_fax']
        contact_out.email = self.cleaned_data['contact_out_email']
        if commit:
            contact_out.save()
            partner_entity.contact_out_id = contact_out.id
        return contact_out

    def save(self, commit=True):
        partner_entity = super(PartnerEntityForm, self).save(commit=False)
        self.save_address(partner_entity, commit=commit)
        self.save_contact_in(partner_entity, commit=commit)
        self.save_contact_out(partner_entity, commit=commit)
        if commit:
            partner_entity.save()
            self.save_m2m()
        return partner_entity


class ContactForm(forms.ModelForm):

    class Meta:
        model = Contact
        fields = [
            'title',
            'type',
            'last_name',
            'first_name',
            'society',
            'function',
            'phone',
            'mobile_phone',
            'fax',
            'email',
            'comment',
        ]


class PartnerFilterForm(forms.Form):
    name = forms.CharField(
        label=_('Name'),
        widget=forms.TextInput(attrs={'placeholder': _('partner_name')}),
        required=False,
    )
    partner_type = forms.ModelChoiceField(
        label=_('partner_type'),
        queryset=PartnerType.objects.all(),
        required=False,
    )
    pic_code = forms.CharField(
        label=_('pic_code'),
        widget=forms.TextInput(attrs={'placeholder': _('pic_code')}),
        required=False,
    )
    erasmus_code = forms.CharField(
        label=_('erasmus_code'),
        widget=forms.TextInput(attrs={'placeholder': _('erasmus_code')}),
        required=False,
    )
    city = forms.ChoiceField(
        label=_('city'),
        choices=((None, '---------'),),
        widget=autocomplete.Select2(attrs={'data-width': '100%'}),
        required=False,
    )
    country = forms.ModelChoiceField(
        label=_('country'),
        queryset=Country.objects.filter(address__partners__isnull=False).order_by('name').distinct(),
        widget=autocomplete.ModelSelect2(attrs={'data-width': '100%'}),
        required=False,
    )
    continent = forms.ModelChoiceField(
        label=_('continent'),
        queryset=Continent.objects.filter(country__address__partners__isnull=False).order_by('name').distinct(),
        required=False,
    )
    is_ies = forms.NullBooleanField(
        label=_('is_ies'),
        required=False,
        widget=CustomNullBooleanSelect(),
    )
    is_valid = forms.NullBooleanField(
        label=_('is_valid'),
        required=False,
        widget=CustomNullBooleanSelect(),
    )
    is_actif = forms.NullBooleanField(
        label=_('is_actif'),
        required=False,
        widget=CustomNullBooleanSelect(),
    )
    tags = forms.ModelMultipleChoiceField(
        label=_('tags'),
        queryset=PartnerTag.objects.all(),
        widget=autocomplete.ModelSelect2Multiple(attrs={'data-width': '100%'}),
        required=False,
    )

    def __init__(self, *args, **kwargs):
        super(PartnerFilterForm, self).__init__(*args, **kwargs)
        cities = (
            Address.objects
            .filter(partners__isnull=False, city__isnull=False)
            .values_list('city', flat=True)
            .order_by('city')
            .distinct('city')
        )
        self.fields['city'].choices = ((None, '---------'),) + tuple((city, city) for city in cities)


class MediaForm(forms.ModelForm):
    # FIXME Move with Media model to a more generic app

    class Meta:
        model = Media
        fields = '__all__'
        widgets = {
            'name': forms.TextInput(attrs={'placeholder': _('name')}),
            'description': forms.Textarea(attrs={'placeholder': _('description')}),
            'url': forms.URLInput(attrs={'placeholder': _('url')}),
        }

    def clean(self):
        super(MediaForm, self).clean()
        file = self.cleaned_data.get('file', None)
        url = self.cleaned_data.get('url', None)
        if file and url:
            raise forms.ValidationError(_('file_or_url_only'))
        if not file and not url:
            raise forms.ValidationError(_('file_or_url_required'))
        return self.cleaned_data


class AddressForm(forms.ModelForm):
    # FIXME Move with Address model to a more generic app

    class Meta:
        model = Address
        fields = '__all__'
        widgets = {
            'name': forms.TextInput(attrs={'placeholder': _('address_name_help_text')}),
            'address': forms.Textarea(attrs={'placeholder': _('address')}),
            'postal_code': forms.TextInput(attrs={'placeholder': _('postal_code')}),
            'city': forms.TextInput(attrs={'placeholder': _('city')}),
            'country': autocomplete.ModelSelect2(),
        }

    def __init__(self, *args, **kwargs):
        super(AddressForm, self).__init__(*args, **kwargs)
        self.fields['country'].queryset = Country.objects.all().order_by('name')


class PartnershipFilterForm(forms.Form):

    # UCL

    ucl_university = forms.ModelChoiceField(
        label=_('ucl_university'),
        queryset=Entity.objects.filter(partnerships__isnull=False).distinct(),
        empty_label=_('ucl_university'),
        required=False,
        widget=autocomplete.ModelSelect2(
            url='partnerships:autocomplete:ucl_university_filter',
            attrs={
                'data-width': '100%',
                'class': 'resetting',
                'data-reset': '#id_ucl_university_labo',
            },
        ),
    )

    ucl_university_labo = forms.ModelChoiceField(
        label=_('ucl_university_labo'),
        queryset=Entity.objects.filter(partnerships_labo__isnull=False).distinct(),
        empty_label=_('ucl_university_labo_filter'),
        required=False,
        widget=autocomplete.ModelSelect2(
            url='partnerships:autocomplete:ucl_university_labo_filter',
            forward=['ucl_university'],
            attrs={
                'data-width': '100%',
            },
        ),
    )

    university_offers = forms.ModelMultipleChoiceField(
        label=_('university_offers'),
        queryset=EducationGroupYear.objects.select_related('academic_year')
        .filter(partnerships__isnull=False).distinct(),
        required=False,
        widget=autocomplete.ModelSelect2Multiple(
            url='partnerships:autocomplete:university_offers_filter',
            forward=['ucl_university_labo'],
            attrs={'data-width': '100%'},
        ),
    )

    # Partner

    partner = forms.ModelChoiceField(
        label=_('partner'),
        queryset=Partner.objects.filter(partnerships__isnull=False).distinct(),
        empty_label=_('partner'),
        widget=autocomplete.ModelSelect2(
            attrs={
                'data-width': '100%',
                'class': 'resetting',
                'data-reset': '#id_partner_entity',
            },
            url='partnerships:autocomplete:partner_partnerships_filter',
        ),
        required=False,
    )
    partner_entity = forms.ModelChoiceField(
        label=_('partner_entity'),
        queryset=PartnerEntity.objects.filter(partnerships__isnull=False).distinct(),
        empty_label=_('partner_entity'),
        widget=autocomplete.ModelSelect2(
            attrs={'data-width': '100%'},
            url='partnerships:autocomplete:partner_entity_partnerships_filter',
            forward=['partner'],
        ),
        required=False,
    )
    partner_type = forms.ModelChoiceField(
        label=_('partner_type'),
        queryset=PartnerType.objects.filter(partners__partnerships__isnull=False).distinct(),
        empty_label=_('partner_type'),
        required=False,
    )
    erasmus_code = forms.CharField(
        label=_('erasmus_code'),
        widget=forms.TextInput(attrs={'placeholder': _('erasmus_code')}),
        required=False,
    )
    city = forms.ChoiceField(
        label=_('city'),
        choices=((None, _('city')),),
        widget=autocomplete.Select2(attrs={'data-width': '100%'}),
        required=False,
    )
    country = forms.ModelChoiceField(
        label=_('country'),

        queryset=(
            Country.objects
            .filter(address__partners__partnerships__isnull=False)
            .order_by('name')
            .distinct()
        ),
        empty_label=_('country'),
        widget=autocomplete.ModelSelect2(attrs={'data-width': '100%'}),
        required=False,
    )
    continent = forms.ModelChoiceField(
        label=_('continent'),
        queryset=(
            Continent.objects
            .filter(country__address__partners__partnerships__isnull=False)
            .order_by('name')
            .distinct()
        ),
        empty_label=_('continent'),
        required=False,
    )
    partner_tags = forms.ModelMultipleChoiceField(
        label=_('partner_tags'),
        queryset=PartnerTag.objects.filter(partners__partnerships__isnull=False).distinct(),
        widget=autocomplete.ModelSelect2Multiple(attrs={'data-width': '100%'}),
        required=False,
    )

    # Partnerships

    education_field = forms.ModelChoiceField(
        label=_('education_field'),
        queryset=PartnershipYearEducationField.objects.filter(partnershipyear__isnull=False).distinct(),
        widget=autocomplete.ModelSelect2(attrs={'data-width': '100%'}),
        required=False,
    )
    education_level = forms.ModelChoiceField(
        label=_('education_level'),
        queryset=PartnershipYearEducationLevel.objects.filter(partnershipyear__isnull=False).distinct(),
        widget=autocomplete.ModelSelect2(attrs={'data-width': '100%'}),
        required=False,
    )
    is_sms = forms.NullBooleanField(
        label=_('is_sms'),
        widget=CustomNullBooleanSelect(),
        required=False,
    )
    is_smp = forms.NullBooleanField(
        label=_('is_smp'),
        widget=CustomNullBooleanSelect(),
        required=False,
    )
    is_sta = forms.NullBooleanField(
        label=_('is_sta'),
        widget=CustomNullBooleanSelect(),
        required=False,
    )
    is_stt = forms.NullBooleanField(
        label=_('is_stt'),
        widget=CustomNullBooleanSelect(),
        required=False,
    )
    partnership_type = forms.ChoiceField(
        label=_('partnership_type'),
        choices=((None, '---------'),) + PartnershipYear.TYPE_CHOICES,
        required=False,
    )
    supervisor = forms.ModelChoiceField(
        label=_('partnership_supervisor'),
        queryset=Person.objects.filter(partnerships_supervisor__isnull=False).distinct(),
        widget=autocomplete.ModelSelect2(attrs={'data-width': '100%'}),
        required=False,
    )
    tags = forms.ModelMultipleChoiceField(
        label=_('tags'),
        queryset=PartnershipTag.objects.all(),
        widget=autocomplete.ModelSelect2Multiple(attrs={'data-width': '100%'}),
        required=False,
    )

    partnership_in = forms.ModelChoiceField(
        label=_('partnership_in'),
        help_text=_('parnership_in_help_text'),
        queryset=AcademicYear.objects.all(),
        required=False,
    )
    partnership_ending_in = forms.ModelChoiceField(
        label=_('partnership_ending_in'),
        queryset=AcademicYear.objects.all(),
        required=False,
    )
    partnership_valid_in = forms.ModelChoiceField(
        label=_('partnership_valid_in'),
        queryset=AcademicYear.objects.all(),
        required=False,
    )
    partnership_not_valid_in = forms.ModelChoiceField(
        label=_('partnership_not_valid_in'),
        queryset=AcademicYear.objects.all(),
        required=False,
    )
    comment = forms.CharField(
        label=_('comment'),
        required=False,
    )

    def __init__(self, *args, **kwargs):
        super(PartnershipFilterForm, self).__init__(*args, **kwargs)
        cities = (
            Address.objects
            .filter(partners__partnerships__isnull=False, city__isnull=False)
            .values_list('city', flat=True)
            .order_by('city')
            .distinct('city')
        )
        self.fields['city'].choices = ((None, _('city')),) + tuple((city, city) for city in cities)


class PartnershipForm(forms.ModelForm):

    class Meta:
        model = Partnership
        fields = (
            'partner',
            'partner_entity',
            'ucl_university',
            'ucl_university_labo',
            'supervisor',
            'comment',
            'tags',
        )
        widgets = {
            'partner': autocomplete.ModelSelect2(
                url='partnerships:autocomplete:partner',
                attrs={
                    'class': 'resetting',
                    'data-reset': '#id_partner_entity',
                },
            ),
            'partner_entity': autocomplete.ModelSelect2(
                url='partnerships:autocomplete:partner_entity',
                forward=['partner'],
            ),
            'ucl_university': autocomplete.ModelSelect2(
                url='partnerships:autocomplete:ucl_university',
                attrs={
                    'class': 'resetting',
                    'data-reset': '#id_ucl_university_labo',
                },
            ),
            'ucl_university_labo': autocomplete.ModelSelect2(
                url='partnerships:autocomplete:ucl_university_labo',
                forward=['ucl_university'],
            ),
            'supervisor': autocomplete.ModelSelect2(
                url='partnerships:autocomplete:person',
                attrs={'data-placeholder': _('same_supervisor_than_management_entity')},
            ),
            'tags': autocomplete.Select2Multiple(),
        }

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user')
        super(PartnershipForm, self).__init__(*args, **kwargs)
        if not user_is_adri(self.user):
            # Restrict fields for GF
            self.fields['ucl_university'].queryset = Entity.objects.filter(entitymanager__person__user=self.user)
            if self.instance.pk is not None:
                self.fields['partner'].disabled = True
                self.fields['ucl_university'].disabled = True
                self.fields['ucl_university_labo'].disabled = True
                self.fields['supervisor'].disabled = True
                self.fields['comment'].disabled = True
                self.fields['tags'].disabled = True

        self.fields['ucl_university'].queryset = self.fields['ucl_university'].queryset.distinct()

        try:
            self.fields['partner'].widget.forward.append(forward.Const(self.instance.partner.pk, 'partner_pk'))
        except Partner.DoesNotExist:
            pass

    def clean_partner(self):
        partner = self.cleaned_data['partner']
        if self.instance.pk and partner == self.instance.partner:
            return partner
        if not partner.is_actif:
            raise ValidationError(_('partnership_inactif_partner_error'))
        return partner

    def clean(self):
        super(PartnershipForm, self).clean()
        partner = self.cleaned_data.get('partner', None)
        partner_entity = self.cleaned_data.get('partner_entity', None)
        ucl_university = self.cleaned_data.get('ucl_university', None)
        ucl_university_labo = self.cleaned_data.get('ucl_university_labo', None)

        if partner_entity and partner_entity.partner != partner:
            self.add_error('partner_entity', _('invalid_partner_entity'))

        if (
            ucl_university_labo
            and not ucl_university_labo.entityversion_set.filter(parent=ucl_university).exists()
        ):
            self.add_error('ucl_university_labo', _('invalid_ucl_university_labo'))
        return self.cleaned_data


class PartnershipYearForm(forms.ModelForm):

    # Used for the dal forward
    faculty = forms.CharField(widget=forms.HiddenInput())

    start_academic_year = forms.ModelChoiceField(
        label=_('start_academic_year'),
        queryset=AcademicYear.objects.all(),
        required=True,
    )
    from_academic_year = forms.ModelChoiceField(
        label=_('from_academic_year'),
        queryset=AcademicYear.objects.all(),
        required=True,
    )
    end_academic_year = forms.ModelChoiceField(
        label=_('end_academic_year'),
        queryset=AcademicYear.objects.all(),
        required=True,
    )

    offers = EducationGroupYearChoiceSelect(
        queryset=EducationGroupYear.objects.filter(university_certificate=True),
        widget=autocomplete.ModelSelect2Multiple(
            url='partnerships:autocomplete:partnership_year_offers',
        ),
    )

    class Meta:
        model = PartnershipYear
        fields = (
            'partnership_type',
            'education_fields',
            'education_levels',
            'entities',
            'offers',
            'is_sms',
            'is_smp',
            'is_sta',
            'is_stt',
        )
        widgets = {
            'education_fields': autocomplete.ModelSelect2Multiple(),
            'education_levels': autocomplete.ModelSelect2Multiple(),
            'entities': autocomplete.ModelSelect2Multiple(
                url='partnerships:autocomplete:partnership_year_entities',
                forward=['faculty'],
            ),
        }

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user')
        super(PartnershipYearForm, self).__init__(*args, **kwargs)
        self.fields['partnership_type'].initial = PartnershipYear.TYPE_MOBILITY
        self.fields['partnership_type'].disabled = True
        current_academic_year = (
            PartnershipConfiguration.get_configuration().get_current_academic_year_for_creation_modification()
        )
        is_adri = user_is_adri(self.user)
        if not is_adri:
            if current_academic_year is not None:
                future_academic_years = AcademicYear.objects.filter(year__gte=current_academic_year.year)
                self.fields['start_academic_year'].queryset = future_academic_years
                self.fields['from_academic_year'].queryset = future_academic_years
                self.fields['end_academic_year'].queryset = future_academic_years
        try:
            # Update
            self.fields['end_academic_year'].initial = self.instance.partnership.end_academic_year
            if is_adri:
                self.fields['start_academic_year'].initial = self.instance.partnership.start_academic_year
            else:
                del self.fields['start_academic_year']
            self.fields['from_academic_year'].initial = current_academic_year
        except Partnership.DoesNotExist:
            # Create
            self.fields['start_academic_year'].initial = current_academic_year
            del self.fields['from_academic_year']
            self.fields['end_academic_year'].initial = current_academic_year

    def clean(self):
        super(PartnershipYearForm, self).clean()
        if self.cleaned_data['is_sms'] or self.cleaned_data['is_smp']:
            if not self.cleaned_data['education_levels']:
                self.add_error('education_levels', ValidationError(_('education_levels_empty_errors')))
        else:
            self.cleaned_data['education_levels'] = []
            self.cleaned_data['entities'] = []
            self.cleaned_data['offers'] = []
        start_academic_year = self.cleaned_data.get('start_academic_year', None)
        from_academic_year = self.cleaned_data.get('from_academic_year', None)
        end_academic_year = self.cleaned_data.get('end_academic_year', None)
        if start_academic_year is not None:
            if start_academic_year.year > end_academic_year.year:
                self.add_error('start_academic_year', ValidationError(_('start_date_after_end_date')))
            if from_academic_year is not None and start_academic_year.year > from_academic_year.year:
                self.add_error('start_academic_year', ValidationError(_('start_date_after_from_date')))
        if from_academic_year is not None and from_academic_year.year > end_academic_year.year:
            self.add_error('from_academic_year', ValidationError(_('from_date_after_end_date')))
        return self.cleaned_data


class PartnershipAgreementForm(forms.ModelForm):

    class Meta:
        model = PartnershipAgreement
        fields = [
            'start_academic_year',
            'end_academic_year',
            'status',
            'eligible',
            'comment',
        ]

    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user')
        super(PartnershipAgreementForm, self).__init__(*args, **kwargs)
        if not user_is_adri(user):
            del self.fields['status']
            del self.fields['eligible']

    def clean(self):
        super(PartnershipAgreementForm, self).clean()
        if self.cleaned_data['start_academic_year'].year > self.cleaned_data['end_academic_year'].year:
            self.add_error('start_academic_year', ValidationError(_('start_date_after_end_date')))
            self.add_error('end_academic_year', ValidationError(_('start_date_after_end_date')))
        return self.cleaned_data


class PartnershipConfigurationForm(forms.ModelForm):

    class Meta:
        model = PartnershipConfiguration
        fields = [
            'partnership_creation_update_max_date_day',
            'partnership_creation_update_max_date_month',
        ]

    def clean(self):
        super(PartnershipConfigurationForm, self).clean()
        try:
            date(
                2001,
                self.cleaned_data['partnership_creation_update_max_date_month'],
                self.cleaned_data['partnership_creation_update_max_date_day'],
            )
        except ValueError:
            self.add_error(
                'partnership_creation_update_max_date_day',
                ValidationError(_('invalid_partnership_creation_max_date'))
            )
        return self.cleaned_data


class UCLManagementEntityForm(forms.ModelForm):
    class Meta:
        model = UCLManagementEntity
        fields = [
            'faculty',
            'entity',
            'administrative_responsible',
            'academic_responsible',
            'contact_in_person',
            'contact_in_email',
            'contact_in_url',
            'contact_out_person',
            'contact_out_email',
            'contact_out_url',
        ]
        widgets = {
            'faculty': autocomplete.ModelSelect2(
                url='partnerships:autocomplete:faculty',
                attrs={
                    'class': 'resetting',
                    'data-reset': '#id_entity',
                },
            ),
            'entity': autocomplete.ModelSelect2(
                url='partnerships:autocomplete:faculty_entity',
                forward=(forward.Field('faculty', 'ucl_university'),),
            ),
            'administrative_responsible': autocomplete.ModelSelect2(
                url='partnerships:autocomplete:person',
            ),
            'academic_responsible': autocomplete.ModelSelect2(
                url='partnerships:autocomplete:person',
            ),
            'contact_in_person': autocomplete.ModelSelect2(
                url='partnerships:autocomplete:person',
            ),
            'contact_out_person': autocomplete.ModelSelect2(
                url='partnerships:autocomplete:person',
            ),
        }

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        if (self.instance.pk is not None and self.instance.faculty.partnerships.exists()) or (
            self.user is not None and not user_is_adri(self.user)
        ):
            self.fields['entity'].disabled = True
            self.fields['faculty'].disabled = True
        if self.user is not None and not user_is_adri(self.user):
            self.fields['academic_responsible'].disabled = True
            self.fields['administrative_responsible'].disabled = True
