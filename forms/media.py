from django import forms
from django.utils.translation import gettext_lazy as _

from partnership.models import Media

__all__ = ['MediaForm']


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
        super().clean()
        file = self.cleaned_data.get('file', None)
        url = self.cleaned_data.get('url', None)
        if file and url:
            raise forms.ValidationError(_('file_or_url_only'))
        if not file and not url:
            raise forms.ValidationError(_('file_or_url_required'))
        return self.cleaned_data
