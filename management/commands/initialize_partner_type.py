import argparse
import csv

from django.core.management import BaseCommand

from partnership.management.commands.progress_bar import ProgressBarMixin
from partnership.models import Partner


class Command(ProgressBarMixin, BaseCommand):

    line = -1

    def add_arguments(self, parser):
        parser.add_argument(
            'csv_file', type=argparse.FileType('r'), help='partner_types.csv',
        )

    def write_error(self, message):
        self.stderr.write('(line {line}) {message}'.format(
            line=self.line, message=message)
        )

    def handle(self, *args, **options):
        lines = []
        csv_reader = csv.reader(options['csv_file'], delimiter=';')
        next(csv_reader)  # Header
        for row in csv_reader:
            lines.append(row)
        total = len(lines)
        self.print_progress_bar(0, total)
        for i, line in enumerate(lines, start=1):
            self.line = i + 1
            partner_id = line[0]
            partner_type_id = line[6]
            try:
                Partner.objects.filter(id=partner_id).update(
                    partner_type_id=partner_type_id
                )
            except Exception as e:
                self.write_error(str(e))
            self.print_progress_bar(i, total)
