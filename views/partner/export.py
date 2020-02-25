from django.contrib.auth.mixins import PermissionRequiredMixin
from django.contrib.postgres.aggregates import StringAgg
from django.utils.timezone import now
from django.utils.translation import gettext, gettext_lazy as _

from partnership.views import ExportView
from .mixins import PartnersListFilterMixin

__all__ = [
    'PartnersExportView',
]


class PartnersExportView(PermissionRequiredMixin, PartnersListFilterMixin, ExportView):
    login_url = 'access_denied'
    permission_required = 'partnership.can_access_partnerships'

    def get_xls_headers(self):
        return [
            gettext('id'),
            gettext('external_id'),
            gettext('author'),
            gettext('created'),
            gettext('changed'),
            gettext('Name'),
            gettext('is_valid'),
            gettext('partner_start_date'),
            gettext('partner_end_date'),
            gettext('now_known_as'),
            gettext('partner_type'),
            gettext('pic_code'),
            gettext('erasmus_code'),
            gettext('is_ies'),
            gettext('use_egracons'),
            gettext('city'),
            gettext('country'),
            gettext('tags'),
        ]

    def get_xls_data(self):
        queryset = self.get_queryset()
        queryset = (
            queryset
            .annotate(tags_list=StringAgg('tags__value', ', '))
            .values_list(
                'id',
                'external_id',
                'author__username',
                'created',
                'changed',
                'name',
                'is_valid',
                'start_date',
                'end_date',
                'now_known_as__name',
                'partner_type__value',
                'pic_code',
                'erasmus_code',
                'is_ies',
                'use_egracons',
                'contact_address__city',
                'contact_address__country__name',
                'tags_list',
            )
        )
        return queryset.distinct()

    def get_description(self):
        return _('partners')

    def get_filename(self):
        return now().strftime('partners-%Y-%m-%d-%H-%M-%S')

    def get_title(self):
        return _('partners')