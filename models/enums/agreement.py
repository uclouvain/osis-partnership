from django.utils.translation import gettext_lazy as _

from base.models.utils.utils import ChoiceEnum


class AgreementStatus(ChoiceEnum):
    WAITING = _('status_waiting')
    VALIDATED = _('status_validated')
    REFUSED = _('status_refused')
