from django.utils.translation import gettext_lazy as _

from base.models.utils.utils import ChoiceEnum


class DateFilterType(ChoiceEnum):
    ONGOING = _('ongoing')
    STOPPING = _('stopping')
