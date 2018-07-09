import csv
from datetime import date

from django.contrib.auth.models import User
from django.core.management import BaseCommand
from django.db import transaction, IntegrityError

from partnership.models import Partner, Address, Media, PartnerType
from reference.models.country import Country

COUNTRIES_OLD_TO_ISO = {
    'ZA': 'ZA',
    'ALB': 'AL',
    'DZ': 'DZ',
    'D': 'DE',
    'AND': 'AD',
    'AR': 'AR',
    'AM': 'AM',
    'AU': 'AU',
    'A': 'AT',
    'AZ': 'AZ',
    'BS': 'BS',
    'BD': 'BD',
    'BY': 'BY',
    'B': 'BE',
    'BJ': 'BJ',
    'BO': 'BO',
    'BA': 'BA',
    'BR': 'BR',
    'BG': 'BG',
    'BF': 'BF',
    'BI': 'BI',
    'CV': 'CV',
    'KH': 'KH',
    'CM': 'CM',
    'CA': 'CA',
    'CL': 'CL',
    'CN': 'CN',
    'CY': 'CY',
    'CO': 'CO',
    'CR': 'CR',
    'CI': 'CI',
    'HR': 'HR',
    'CU': 'CU',
    'CW': 'CW',
    'DK': 'DK',
    'EG': 'EG',
    'SV': 'SV',
    'AE': 'AE',
    'EC': 'EC',
    'E': 'ES',
    'EE': 'EE',
    'US': 'US',
    'SF': 'FI',
    'F': 'FR',
    'GE': 'GE',
    'G': 'EL',
    'GY': 'GN',
    'GF': 'GF',
    'HU': 'HU',
    'MU': 'MU',
    'IN': 'IN',
    'ID': 'ID',
    'IRL': 'IE',
    'IS': 'IS',
    'IL': 'IL',
    'I': 'IT',
    'JP': 'JP',
    'KZ': 'KZ',
    'KE': 'KE',
    'KG': 'KG',
    'LA': 'LA',
    'LV': 'LV',
    'LB': 'LB',
    'FL': 'LI',
    'LT': 'LT',
    'LUX': 'LU',
    'MC': 'MO',
    'MK': 'MK',
    'MG': 'MG',
    'MY': 'MY',
    'ML': 'ML',
    'MT': 'MT',
    'MA': 'MA',
    'MX': 'MX',
    'MOL': 'MD',
    'MN': 'MN',
    'NP': 'NP',
    'NI': 'NI',
    'N': 'NO',
    'NZ': 'NZ',
    'UG': 'UG',
    'UZ': 'UZ',
    'PK': 'PK',
    'PA': 'PA',
    'PY': 'PY',
    'NL': 'NL',
    'PE': 'PE',
    'PH': 'PH',
    'PL': 'PL',
    'P': 'PT',
    'CD': 'CD',
    'KR': 'KR',
    'DO': 'DO',
    'CZ': 'CZ',
    'RO': 'RO',
    'UK': 'UK',
    'RU': 'RU',
    'RW': 'RW',
    'SN': 'SN',
    'SP': 'SG',
    'SK': 'SK',
    'SI': 'SI',
    'S': 'SE',
    'CH': 'CH',
    'SR': 'SR',
    'TW': 'TW',
    'TZ': 'TZ',
    'TH': 'TH',
    'TG': 'TG',
    'TN': 'TN',
    'TR': 'TR',
    'UKR': 'UA',
    'UY': 'UY',
    'VE': 'VE',
    'VN': 'VN',
}


class Command(BaseCommand):

    line = -1
    default_values = None

    # Cache

    countries = {}
    partners_by_code = {}

    def add_arguments(self, parser):
        parser.add_argument('csv_filepath', type=str)

    def write_error(self, message):
        self.stderr.write('(line {line}) {message}'.format(line=self.line, message=message))

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

    def parse_date(self, date_string):
        if not date_string:
            return None
        day, month, year = map(int, date_string.split('/'))
        return date(year, month, day)

    def get_default_value(self):
        if self.default_values is None:
            partner_type = PartnerType.objects.all().first()
            if partner_type is None:
                partner_type = PartnerType.objects.create(value='IMPORTED')
            self.default_values = {
                'author': User.objects.filter(person__personentity__entity__entityversion__acronym='ADRI').first(),
                'partner_type': partner_type,
                'website': 'https://uclouvain.be',
            }
        return self.default_values

    def get_country(self, old_code):
        if not old_code:
            return None
        if old_code not in self.countries:
            iso = COUNTRIES_OLD_TO_ISO.get(old_code, None)
            if iso is None:
                self.write_error('Unknown old country code {code}'.format(code=old_code))
                self.countries[old_code] = None
            else:
                try:
                    self.countries[old_code] = Country.objects.get(iso_code=iso)
                except Country.DoesNotExist:
                    self.write_error('Unknown country for iso {iso}'.format(iso=iso))
                    self.countries[old_code] = None
        return self.countries[old_code]

    @transaction.atomic
    def import_partner(self, line):
        if not line[1]:
            self.write_error('No EPC id for {0}'.format(line[6]))
            return
        external_id = int(line[1])
        try:
            partner = Partner.objects.get(external_id=external_id)
        except Partner.DoesNotExist:
            partner = Partner(external_id=external_id)

        # Mandatory fields not in the CSV file
        default_values = self.get_default_value()
        partner.author = default_values['author']
        partner.partner_type = default_values['partner_type']

        # Fields from the CSV file
        partner.partner_code = line[2] if line[2] else None
        partner.pic_code = line[3] if line[3] else None
        partner.erasmus_code = line[4] if line[4] else None
        partner.name = line[6] if line[6] else None
        partner.start_date = self.parse_date(line[7])
        partner.end_date = self.parse_date(line[8])
        partner.is_ies = line[11] == 'U'
        if partner.contact_address is None:
            partner.contact_address = Address()
        partner.contact_address.address = line[12]
        partner.email = line[13] if line[13] else None
        partner.is_nonprofit = line[14] == 'YES'
        partner.is_public = line[15] == 'YES'
        partner.phone = line[16] if line[16] else None
        partner.contact_type = line[17] if line[17] else None
        partner.website = line[18] if line[18] else default_values['website']
        partner.contact_address.city = line[19] if line[19] else None
        partner.contact_address.country = self.get_country(line[22])
        partner.use_egracons = line[23] == 'YES'

        # Save
        partner.contact_address.save()
        partner.contact_address_id = partner.contact_address.id
        try:
            partner.save()
        except IntegrityError as e:
            self.write_error('Error while importing partner {0}: {1}'.format(partner.name, str(e)))
            return

        # Médias
        def add_media(partner, url, name):
            if not url:
                return
            if partner.medias.filter(url=url).exists():
                return
            media = Media.objects.create(
                name=name,
                url=url,
                visibility=Media.VISIBILITY_STAFF,
                author=default_values['author'],
            )
            partner.medias.add(media)
        add_media(partner, line[26], "Fiche d'évaluation")
        add_media(partner, line[28], "Fiche d'évaluation 2013")
        add_media(partner, line[30], "Fiche d'évaluation 2017")

        self.partners_by_code[partner.partner_code] = partner

    def import_partner_now_known_as(self, line):
        now_known_as = line[10]
        if not now_known_as or line[2] not in self.partners_by_code:
            return
        if now_known_as not in self.partners_by_code:
            self.write_error("Unknown partner {partner}".format(partner=now_known_as))
            return
        partner = self.partners_by_code[line[2]]
        partner.now_known_as = self.partners_by_code[now_known_as]
        partner.save()

    def handle(self, *args, **options):
        # Init
        csv_filepath = options['csv_filepath']
        # Read CSV file
        # We may need to do that on the fly if the files are too big
        lines = []
        with open(csv_filepath, 'r') as csv_file:
            csv_reader = csv.reader(csv_file, delimiter=';')
            header = next(csv_reader)
            # # Format is temporary for now
            # if header != self.header:
            #     self.write_error("Bad Header: {0}".format(header))
            #     return
            for row in csv_reader:
                lines.append(row)
        # Import
        self.stdout.write("Importing partners 1/2")
        total_lines_number = len(lines)
        self.print_progress_bar(0, total_lines_number)
        for (index, line) in enumerate(lines, 1):
            self.line = index + 1
            self.import_partner(line)
            self.print_progress_bar(index, total_lines_number)

        # Import now_known_as
        self.stdout.write("Importing partners est_devenu_fait_partie_de 2/2")
        self.print_progress_bar(0, total_lines_number)
        for (index, line) in enumerate(lines, 1):
            self.line = index + 1
            self.import_partner_now_known_as(line)
            self.print_progress_bar(index, total_lines_number)
