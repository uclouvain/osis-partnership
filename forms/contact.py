from django import forms

from partnership.models import Contact

__all__ = ['ContactForm']


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
