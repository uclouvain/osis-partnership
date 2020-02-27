from django.utils.translation import gettext_lazy as _

from base.models.utils.utils import ChoiceEnum


class MediaVisibility(ChoiceEnum):
    PUBLIC = _('visibility_public')
    STAFF = _('visibility_staff')
    STAFF_STUDENT = _('visibility_staff_student')
