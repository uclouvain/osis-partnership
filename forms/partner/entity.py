from django import forms
from django.utils.translation import gettext_lazy as _

from partnership.models import Address, Contact, PartnerEntity
from reference.models.country import Country

__all__ = ['PartnerEntityForm']


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
        super().__init__(*args, **kwargs)
        self.fields['parent'].queryset = PartnerEntity.objects.filter(
            partner=partner,
        ).exclude(pk=self.instance.pk)

    def get_initial_for_field(self, field, field_name):
        """ Set value of foreign keys fields """
        value = super().get_initial_for_field(field, field_name)
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
        partner_entity = super().save(commit=False)
        self.save_address(partner_entity, commit=commit)
        self.save_contact_in(partner_entity, commit=commit)
        self.save_contact_out(partner_entity, commit=commit)
        if commit:
            partner_entity.save()
            self.save_m2m()
        return partner_entity
