import argparse
import csv

from django.core.management import BaseCommand

from partnership.models import Partner


class Command(BaseCommand):

    line = -1

    def add_arguments(self, parser):
        parser.add_argument(
            'csv_file', type=argparse.FileType('r'), help='partner_types.csv',
        )

    def print_progress_bar(self, iteration, total, prefix='', suffix='', decimals=1, length=100, fill='█'):
        """
        From http://stackoverflow.com/a/34325723/2575355

        Call in a loop to create terminal progress bar
        @params:
            iteration   - Required  : current iteration (Int)
            total       - Required  : total iterations (Int)
            prefix      - Optional  : prefix string (Str)
            suffix      - Optional  : suffix string (Str)
            decimals    - Optional  : positive number of decimals in percent complete (Int)
            length      - Optional  : character length of bar (Int)
            fill        - Optional  : bar fill character (Str)
        """
        percent = ("{0:." + str(decimals) + "f}").format(100 * (iteration / float(total)))
        filled_length = int(length * iteration // total)
        bar = fill * filled_length + '-' * (length - filled_length)
        self.stdout.write('\r%s |%s| %s%% %s' % (prefix, bar, percent, suffix), ending='\r')
        # Print New Line on Complete
        if iteration == total:
            self.stdout.write('')

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
                Partner.objects.filter(id=partner_id).update(partner_type_id=partner_type_id)
            except Exception as e:
                self.write_error(str(e))
            self.print_progress_bar(i, total)
