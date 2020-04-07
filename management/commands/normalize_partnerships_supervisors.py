from django.core.management import BaseCommand
from django.db.models import Q

from partnership.management.commands.progress_bar import ProgressBarMixin
from partnership.models import Partnership, UCLManagementEntity


class Command(ProgressBarMixin, BaseCommand):
    def handle(self, *args, **options):
        total = UCLManagementEntity.objects.count()
        self.print_progress_bar(0, total)
        entities = UCLManagementEntity.objects.all()
        for i, management_entity in enumerate(entities):
            Partnership.objects.filter(
                Q(ucl_university=management_entity.entity_id)
                | Q(ucl_university_labo=management_entity.entity_id),
                supervisor=management_entity.academic_responsible_id,
            ).update(supervisor=None)
            self.print_progress_bar(i + 1, total)
