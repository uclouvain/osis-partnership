from django.core.management import BaseCommand

from partnership.models import UCLManagementEntity, Partnership


class Command(BaseCommand):

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

    def handle(self, *args, **options):
        total = UCLManagementEntity.objects.count()
        self.print_progress_bar(0, total)
        for i, management_entity in enumerate(UCLManagementEntity.objects.all()):
            queryset = Partnership.objects.filter(ucl_university=management_entity.faculty_id)
            if management_entity.entity_id is None:
                queryset = queryset.filter(ucl_university_labo__isnull=True)
            else:
                queryset = queryset.filter(ucl_university_labo=management_entity.entity_id)
            queryset = queryset.filter(supervisor=management_entity.academic_responsible_id)
            queryset.update(supervisor=None)
            self.print_progress_bar(i + 1, total)
