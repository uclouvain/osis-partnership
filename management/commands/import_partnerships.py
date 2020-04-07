import csv
import os
from datetime import date

from django.core.management import BaseCommand
from django.db import IntegrityError, transaction

from base.models.academic_year import AcademicYear
from base.models.entity import Entity
from base.models.person import Person
from partnership.management.commands.progress_bar import ProgressBarMixin
from partnership.models import (
    Address, Media, Partner, Partnership,
    PartnershipAgreement, PartnershipYear,
    PartnershipYearEducationField, PartnerType,
    UCLManagementEntity, MediaVisibility, PartnershipType, AgreementStatus,
)
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


class Command(ProgressBarMixin, BaseCommand):

    line = -1
    filename = ''
    default_values = None

    # Cache

    countries = {}
    supervisors = {}
    entities = {}
    education_fields = {}
    academic_years = {}
    partners_by_code = {}
    partners_by_csv_id = {}
    partnerships_for_agreements = {}

    def add_arguments(self, parser):
        parser.add_argument(
            'csv_folder', type=str, help='folder containing partenaires.csv, '
                                         'partenariats.csv and accords.csv',
        )

    def handle(self, *args, **options):
        # Init
        csv_folder = options['csv_folder']

        # Read CSV files
        # We may need to do that on the fly if the files are too big
        self.stdout.write("Reading files 1/5")
        partners_lines = self.import_file(csv_folder, 'partenaires.csv')
        partnerships_lines = self.import_file(csv_folder, 'partenariats.csv')
        agreements_lines = self.import_file(csv_folder, 'accords.csv')

        # Import partners
        self.stdout.write("Importing partners 2/5")
        self.filename = 'partenaires.csv'
        total_lines_number = len(partners_lines)
        self.print_progress_bar(0, total_lines_number)
        for (index, line) in enumerate(partners_lines, 1):
            self.line = index + 1
            self.import_partner(line)
            self.print_progress_bar(index, total_lines_number)

        # Import partners now_known_as
        self.stdout.write("Importing partners est_devenu_fait_partie_de 3/5")
        self.print_progress_bar(0, total_lines_number)
        for (index, line) in enumerate(partners_lines, 1):
            self.line = index + 1
            self.import_partner_now_known_as(line)
            self.print_progress_bar(index, total_lines_number)

        # Import partnerships
        self.stdout.write("Importing partnerships 4/5")
        self.filename = 'partenariats.csv'
        total_lines_number = len(partnerships_lines)
        self.print_progress_bar(0, total_lines_number)
        for (index, line) in enumerate(partnerships_lines, 1):
            self.line = index + 1
            self.import_partnership(line)
            self.print_progress_bar(index, total_lines_number)

        # Import agreements
        self.stdout.write("Importing agreements 5/5")
        self.filename = 'accords.csv'
        total_lines_number = len(agreements_lines)
        self.print_progress_bar(0, total_lines_number)
        for (index, line) in enumerate(agreements_lines, 1):
            self.line = index + 1
            self.import_agreement(line)
            self.print_progress_bar(index, total_lines_number)

    # HELPERS

    def import_file(self, csv_folder, filename):
        rows = []
        with open(os.path.join(csv_folder, filename)) as csv_file:
            csv_reader = csv.reader(csv_file, delimiter=';')
            next(csv_reader)  # Header
            for row in csv_reader:
                rows.append(row)
        return rows

    def write_error(self, message):
        self.stderr.write('({filename} line {line}) {message}'.format(
            filename=self.filename, line=self.line, message=message)
        )

    def parse_date(self, date_string):
        if not date_string:
            return None
        day, month, year = map(int, date_string.split('/'))
        return date(year, month, day)

    def get_country(self, old_code, line):
        if not old_code:
            return None
        # Fix for bad data in csv
        if old_code == 'PT':
            old_code = 'P'
        if old_code not in self.countries:
            iso = COUNTRIES_OLD_TO_ISO.get(old_code, None)
            if iso is None:
                msg = 'Unknown old country code {code} (fmp_id={fmp_id} ; ' \
                       'nom={nom})'
                self.write_error(msg.format(
                    code=old_code,
                    fmp_id=line[2],
                    nom=line[6],
                ))
                self.countries[old_code] = None
            else:
                # Fix for bad data in csv
                code_fix = {
                    'UK': 'GB',
                    'EL': 'GR',
                    'CW': 'NL',
                }
                if iso in code_fix:
                    iso = code_fix[iso]
                try:
                    country = Country.objects.get(iso_code=iso)
                    self.countries[old_code] = country
                except Country.DoesNotExist:
                    msg = 'Unknown country for iso {iso} (fmp_id={fmp_id} ; ' \
                           'nom={nom})'
                    self.write_error(msg.format(
                        iso=iso,
                        fmp_id=line[2],
                        nom=line[6],
                    ))
                    self.countries[old_code] = None
        return self.countries[old_code]

    # PARTNERS

    def get_default_value(self):
        if self.default_values is None:
            partner_type = PartnerType.objects.all().first()
            if partner_type is None:
                partner_type = PartnerType.objects.create(value='IMPORTED')
            self.default_values = {
                'author': Person.objects.filter(
                    personentity__entity__entityversion__acronym='ADRI'
                )[0],
                'partner_type': partner_type,
                'website': 'https://uclouvain.be',
            }
        return self.default_values

    def get_partner_external_id(self, base_external_id, partner_id):
        if not base_external_id:
            return None
        external_id = base_external_id
        i = 1
        if partner_id is not None:
            queryset = Partner.objects.exclude(pk=partner_id)
        else:
            queryset = Partner.objects
        while queryset.filter(external_id=external_id).exists():
            external_id = '{}-{}'.format(base_external_id, i)
            i += 1
        return external_id

    @transaction.atomic
    def import_partner(self, line):
        if not line[2]:
            self.write_error('No id for {0}'.format(line[6]))
            return
        partner_code = line[2]
        try:
            partner = Partner.objects.get(partner_code=partner_code)
        except Partner.DoesNotExist:
            partner = Partner(partner_code=partner_code)

        # Mandatory fields not in the CSV file
        default_values = self.get_default_value()
        partner.is_valid = True
        partner.author = default_values['author']
        partner.partner_type = default_values['partner_type']

        # Fields from the CSV file
        partner.external_id = self.get_partner_external_id(line[1], partner.pk)
        partner.partner_code = line[2] if line[2] else None
        partner.pic_code = line[3] if line[3] else None
        partner.erasmus_code = (
            line[4] if line[4] and line[4] != line[10] else None
        )
        partner.name = line[6] if line[6] else None
        partner.start_date = self.parse_date(line[7])
        partner.end_date = self.parse_date(line[8])
        partner.is_ies = line[11] == 'U'
        if partner.contact_address is None:
            partner.contact_address = Address()
        partner.contact_address.address = line[12]
        partner.email = line[13] if line[13] else None
        partner.is_nonprofit = None if not line[14] else line[14] == 'YES'
        partner.is_public = None if not line[15] else line[15] == 'YES'
        partner.phone = line[16] if line[16] else None
        partner.contact_type = line[17] if line[17] else None
        partner.website = line[18] if line[18] else default_values['website']
        partner.contact_address.city = line[19] if line[19] else None
        partner.contact_address.country = self.get_country(line[22], line)
        partner.use_egracons = line[23] == 'YES'

        # Save
        partner.contact_address.save()
        partner.contact_address_id = partner.contact_address.id
        try:
            partner.save()
        except IntegrityError as e:
            self.write_error('Error while importing partner {0}: {1}'.format(
                partner.name, str(e))
            )
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
                visibility=MediaVisibility.STAFF.name,
                author=default_values['author'],
            )
            partner.medias.add(media)
        add_media(partner, line[26], "Fiche d'évaluation")
        add_media(partner, line[28], "Fiche d'évaluation 2013")
        add_media(partner, line[30], "Fiche d'évaluation 2017")

        if partner.partner_code:
            self.partners_by_code[partner.partner_code] = partner

        self.partners_by_csv_id[line[0]] = partner

    def import_partner_now_known_as(self, line):
        now_known_as = line[10]
        if not now_known_as or line[2] not in self.partners_by_code:
            return
        if now_known_as not in self.partners_by_code:
            msg = "Unknown partner {partner} (fmp_id={fmp_id} ; nom={nom})"
            self.write_error(msg.format(
                partner=now_known_as,
                fmp_id=line[2],
                nom=line[6],
            ))
            return
        partner = self.partners_by_code[line[2]]
        partner.now_known_as = self.partners_by_code[now_known_as]
        partner.save()

    # PARTNERSHIPS
    def get_education_field(self, code):
        if not code:
            return None
        code = code.rjust(4, '0')
        if code not in self.education_fields:
            try:
                ed_field = PartnershipYearEducationField.objects.get(code=code)
                self.education_fields[code] = ed_field
            except PartnershipYearEducationField.DoesNotExist:
                self.write_error('Unknown education field {code}'.format(
                    code=code)
                )
                self.education_fields[code] = None
        return self.education_fields[code]

    def get_entity_by_acronym(self, acronym):
        if not acronym:
            return None
        if acronym not in self.entities:
            try:
                self.entities[acronym] = (
                    Entity.objects
                        .filter(entityversion__acronym=acronym)
                        .order_by('entityversion__start_date')
                        .last()
                )
            except Entity.DoesNotExist:
                self.write_error('Unknown entity {acronym}'.format(
                    acronym=acronym)
                )
                self.entities[acronym] = None
        return self.entities[acronym]

    def get_supervisor(self, global_id):
        if not global_id:
            return None
        global_id = global_id.strip('\n').rjust(8, '0')

        if global_id not in self.supervisors:
            try:
                supervisor = Person.objects.get(global_id=global_id)
                self.supervisors[global_id] = supervisor
            except Person.DoesNotExist:
                self.write_error('Unknown responsable {global_id}'.format(
                    global_id=global_id)
                )
                self.supervisors[global_id] = None

        return self.supervisors[global_id]

    def get_academic_year(self, year):
        if year not in self.academic_years:
            try:
                self.academic_years[year] = AcademicYear.objects.get(year=year)
            except AcademicYear.DoesNotExist:
                self.academic_years[year] = None
        return self.academic_years[year]

    @transaction.atomic
    def import_partnership(self, line):
        if not line[1]:
            msg = 'Invalid partenariat_id (partenariat_id_osis={0}, ' \
                  'partenariat_id={1})'
            self.write_error(msg.format(
                line[0], line[1],
            ))
            return
        external_id = line[1]
        default_values = self.get_default_value()
        try:
            partnership = Partnership.objects.get(external_id=external_id)
        except Partnership.DoesNotExist:
            partnership = Partnership(external_id=external_id,
                                      author=default_values['author'])

        partner = self.partners_by_csv_id.get(line[5], None)
        if partner is None:
            msg = 'Invalid partenaire_id_osis {partner_id} ' \
                  '(partenariat_id_osis={osis}, ' \
                  'partenariat_id={partenariat_id})'
            self.write_error(msg.format(
                partner_id=line[5],
                osis=line[0],
                partenariat_id=line[1],
            ))
            return

        partnership.partner = partner
        partnership.ucl_university = self.get_entity_by_acronym(line[8])
        partnership.ucl_university_labo = self.get_entity_by_acronym(line[10])
        partnership.supervisor = self.get_supervisor(line[12])
        partnership.save()

        UCLManagementEntity.objects.get_or_create(
            defaults={
                'academic_responsible': partnership.supervisor,
                'administrative_responsible': partnership.supervisor,
            },
            entity=partnership.ucl_university_labo,
        )

        educations_fields = []
        for code in [line[15], line[16], line[17]]:
            education_field = self.get_education_field(code)
            if education_field:
                educations_fields.append(education_field)

        try:
            end_year = int(line[3])
        except ValueError:
            end_year = 2019
        for year in range(2018, end_year):
            academic_year = self.get_academic_year(year)
            if academic_year is None:
                self.write_error(
                    'No academic year for year {year}'.format(year=year)
                )
                continue
            try:
                partnership_year = partnership.years.get(
                    academic_year=academic_year
                )
            except PartnershipYear.DoesNotExist:
                partnership_year = PartnershipYear(
                    partnership=partnership,
                    academic_year=academic_year,
                    partnership_type=PartnershipType.MOBILITY.name
                )
            partnership_year.is_sms = bool(line[13])
            partnership_year.is_sta = bool(line[14])
            partnership_year.save()
            partnership_year.education_fields = educations_fields
            if partnership.ucl_university_labo is not None:
                partnership_year.entities = [partnership.ucl_university_labo]

        key = '{0}-{1}'.format(line[5], line[11])
        self.partnerships_for_agreements[key] = partnership

    # AGREEMENTS

    @transaction.atomic
    def import_agreement(self, line):
        if not line[3]:
            return

        if not line[0]:
            self.write_error('No external id')
            return

        key = '{0}-{1}'.format(line[5], line[7])
        partnership = self.partnerships_for_agreements.get(key, None)
        if partnership is None:
            msg = 'No partnership for partner/fmp {0}-{1} (num_accord={2}, ' \
                   'partenaire_id_osis={3}, entite_fmp={4})'
            self.write_error(msg.format(
                line[5],
                line[7],
                line[0],
                line[5],
                line[7],
            ))
            return

        external_id = line[0]
        default_values = self.get_default_value()
        try:
            agreement = PartnershipAgreement.objects.get(
                external_id=external_id
            )
        except PartnershipAgreement.DoesNotExist:
            agreement = PartnershipAgreement(external_id=external_id)

        try:
            start_year, end_year = map(int, line[1].split('-'))
        except ValueError:
            self.write_error('Invalid couverture {0} (num_accord={1}, '
                             'partenaire_id_osis={2}, entite_fmp={3})'.format(
                line[1],
                line[0],
                line[5],
                line[7],
            ))
            return
        agreement.partnership = partnership
        error_msg = 'Academic year does not exist in OSIS : {0} (' \
                    'num_accord={1}, partenaire_id_osis={2}, entite_fmp={3})'
        try:
            agreement.start_academic_year = AcademicYear.objects.get(
                year=start_year
            )
        except AcademicYear.DoesNotExist:
            self.write_error(error_msg.format(
                start_year,
                line[0],
                line[5],
                line[7],
            ))
            return
        try:
            agreement.end_academic_year = AcademicYear.objects.get(
                year=end_year - 1
            )
        except AcademicYear.DoesNotExist:
            self.write_error(error_msg.format(
                end_year - 1,
                line[0],
                line[5],
                line[7],
            ))
            return

        try:
            media = agreement.media
            if media.name == line[10]:
                media.url = line[11].replace(' ', '%20')
                media.save()
        except Media.DoesNotExist:
            media = Media.objects.create(
                name=line[10],
                url=line[11].replace(' ', '%20'),
                visibility=MediaVisibility.STAFF.name,
                author=default_values['author'],
            )
            media.save()
            agreement.media = media
        agreement.status = AgreementStatus.VALIDATED.name
        agreement.eligible = True
        agreement.save()
