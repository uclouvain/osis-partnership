from django.core.management import BaseCommand

from partnership.management.commands import ProgressBarMixin
from partnership.models import Partnership, UCLManagementEntity


class Command(ProgressBarMixin, BaseCommand):
    def handle(self, *args, **options):
        total = UCLManagementEntity.objects.count()
        self.print_progress_bar(0, total)
        entities = UCLManagementEntity.objects.all()
        for i, management_entity in enumerate(entities):
            queryset = Partnership.objects.filter(
                ucl_university=management_entity.faculty_id
            )
            if management_entity.entity_id is None:
                queryset = queryset.filter(ucl_university_labo__isnull=True)
            else:
                queryset = queryset.filter(
                    ucl_university_labo=management_entity.entity_id
                )
            queryset = queryset.filter(
                supervisor=management_entity.academic_responsible_id
            )
            queryset.update(supervisor=None)
            self.print_progress_bar(i + 1, total)
