from django.utils.translation import gettext_lazy as _

from base.models.utils.utils import ChoiceEnum


class ContactTitle(ChoiceEnum):
    MISTER = _('mister')
    MADAM = _('madame')
