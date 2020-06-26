from django.contrib.postgres.aggregates import StringAgg
from django.db.models import OuterRef, Subquery
from django.utils.timezone import now
from django.utils.translation import gettext, gettext_lazy as _

from base.models.entity_version import EntityVersion
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
        queryset = self.filterset.qs
        queryset = (
            queryset
            .annotate(
                tags_list=StringAgg('tags__value', ', '),
                start_date=Subquery(EntityVersion.objects.filter(
                    entity__organization=OuterRef('organization_id'),
                    parent__isnull=True,
                ).order_by('start_date').values('start_date')[:1]),
                end_date=Subquery(EntityVersion.objects.filter(
                    entity__organization=OuterRef('organization_id'),
                    parent__isnull=True,
                ).order_by('-start_date').values('end_date')[:1]),
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
