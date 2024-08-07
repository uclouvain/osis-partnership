from django.contrib.postgres.aggregates import StringAgg
from django.utils.timezone import now
from django.utils.translation import gettext, gettext_lazy as _, pgettext

from .list import PartnersListView
from ..export import ExportView

__all__ = [
    'PartnersExportView',
]


class PartnersExportView(ExportView, PartnersListView):
    def get_xls_headers(self):
        return [
            gettext('id'),
            gettext('external_id'),
            gettext('author'),
            pgettext('partnership', 'created'),
            gettext('changed'),
            gettext('Name'),
            gettext('is_valid'),
            gettext('partner_start_date'),
            gettext('partner_end_date'),
            gettext('now_known_as'),
            gettext('partner_type'),
            gettext('pic_code'),
            gettext('erasmus_code'),
            gettext('use_egracons'),
            gettext('city'),
            gettext('country'),
            gettext('tags'),
        ]

    def get_xls_data(self):
        queryset = self.filterset.qs
        queryset = (
            queryset
            .annotate(
                tags_list=StringAgg('tags__value', ', '),
            )
            .values_list(
                'id',
                'organization__external_id',
                'author__user__username',
                'created',
                'changed',
                'organization__name',
                'is_valid',
                'start_date',
                'end_date',
                'now_known_as__organization__name',
                'organization__type',
                'pic_code',
                'erasmus_code',
                'use_egracons',
                'organization__entity__entityversion__entityversionaddress__city',
                'organization__entity__entityversion__entityversionaddress__country__name',
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
