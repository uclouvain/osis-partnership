import argparse
import csv
import io
from collections import defaultdict
from datetime import date, timedelta

import requests
from django.conf import settings
from django.contrib.gis.geos import Point
from django.core.management import BaseCommand
from django.db.models import F, Subquery, OuterRef

from base.models.entity_version import EntityVersion
from base.models.entity_version_address import EntityVersionAddress
from partnership.models import Partner
from reference.models.country import Country

ID = "ID"
STREET_NUM = "Numero de rue"
STREET = "Adresse"
ERASMUS = "Code Erasmus"
POSTAL_CODE = "Code postal"
CITY = "Ville"
COUNTRY = "Pays"


class Command(BaseCommand):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.counts = defaultdict(int)

    def add_arguments(self, parser: argparse.ArgumentParser):
        parser.add_argument(
            'csv_file',
            type=argparse.FileType('r', encoding="utf-8-sig"),
        )

    def check_file(self, reader):
        expected_fields = (
            ID, ERASMUS, STREET_NUM, STREET, POSTAL_CODE, CITY, COUNTRY
        )
        try:
            assert all(field in reader.fieldnames for field in expected_fields)
        except AssertionError:
            self.stderr.write(self.style.ERROR(
                'Encoding must be UTF-8\n'
                'Delimiter must be ";"\n'
                'Column names must contain {}\n'
                'Headers detected : {}'.format(
                    ", ".join(expected_fields), reader.fieldnames
                )
            ))
        return True

    @staticmethod
    def get_existing_partner_addresses():
        queryset = EntityVersionAddress.objects.filter(
            entity_version__entity__organization__partner__isnull=False,
            entity_version__end_date__isnull=True,
        ).annotate(
            partner_id=F('entity_version__entity__organization__partner__id'),
        ).select_related(
            'country',
            'entity_version'
        ).order_by('-entity_version__start_date')
        partners = {}
        for record in queryset:
            if record.partner_id not in partners:
                partners[record.partner_id] = record

        return partners

    def handle(self, *args, **options):
        file: io.TextIOWrapper = options['csv_file']
        reader = csv.DictReader(file, delimiter=';')

        if not self.check_file(reader):
            return

        partners = self.get_existing_partner_addresses()

        entity_ids = dict(list(Partner.objects.annotate(
            entity_id=Subquery(
                EntityVersion.objects.filter(
                    entity__organization=OuterRef('organization_id'),
                    parent__isnull=True,
                ).order_by('-start_date').values('entity_id')[:1]
            ),
        ).values_list('pk', 'entity_id')))

        country_names = dict(list(Country.objects.values_list('name', 'pk')))

        for row in reader:
            # We need at least the street to update
            if not row[STREET]:
                if options['verbosity'] >= 2:
                    self.stdout.write(self.style.WARNING(
                        'Skipping partner id {}: no address'.format(row[ID])
                    ))
                continue

            # Country name must exist
            if row[COUNTRY] not in country_names:
                self.counts['skipped'] += 1
                self.stderr.write(self.style.ERROR(
                    'Skipping partner id {}: country {} does not exist'.format(
                        row[ID], row[COUNTRY],
                    )
                ))
                continue

            # Check that the address has changed
            existing_address = partners[int(row[ID])] if int(row[ID]) in partners else None
            if self._is_address_unchanged(row, existing_address):
                if options['verbosity'] >= 2:
                    self.stdout.write(self.style.WARNING(
                        'Skipping partner id {}: same address'.format(row[ID])
                    ))
                self.counts['existing'] += 1
                continue

            parts = [
                row[STREET_NUM],
                row[STREET],
                row[POSTAL_CODE],
                row[CITY],
                row[COUNTRY],
            ]
            search = ' '.join(filter(None, parts))

            response = requests.get(settings.GEOCODING_URL, {
                'address': search,
                'language': 'fr',
            }, headers={
                'Authorization': 'Bearer {}'.format(settings.GEOCODING_TOKEN),
            })
            results = response.json()['results']
            if not results:
                self.counts['not_found'] += 1
                self.stderr.write(self.style.ERROR(
                    'Address not found for partner id {:>4} not found: {}'.format(
                        row[ID], search,
                    )
                ))
                continue

            if len(results) > 1:
                self.counts['warning'] += 1
                self.stdout.write(self.style.WARNING(
                    'Multiple results for partner id {}'.format(row[ID])
                ))
            location = results[0]['geometry']['location']
            if options['verbosity'] >= 2:
                self.stdout.write(self.style.SUCCESS(
                    'Address found for partner id {:>4} : {}, {}'.format(
                        row[ID], location['lat'], location['lng'],
                    )
                ))

            # Handle entity version
            last_version = None
            if existing_address:
                last_version = self._override_current_version(existing_address)

            if not last_version:
                # Create a new entity version
                last_version = EntityVersion.objects.create(
                    entity_id=entity_ids[int(row[ID])],
                    parent=None,
                    start_date=date.today(),
                    end_date=None,
                )

            # Create the address
            EntityVersionAddress.objects.create(
                street_number=row[STREET_NUM],
                street=row[STREET],
                postal_code=row[POSTAL_CODE],
                city=row[CITY],
                location=Point(
                    location['lng'],
                    location['lat'],
                ),
                country_id=country_names[row[COUNTRY]],
                entity_version=last_version,
            )
            self.counts['updated'] += 1

        self.stdout.write(self.style.SUCCESS(
            'Updated: {}\nNot found: {}\nSkipped: {}\nWarnings: {}\nExisting: {}'.format(
                self.counts['updated'],
                self.counts['not_found'],
                self.counts['skipped'],
                self.counts['warning'],
                self.counts['existing'],
            )
        ))

    @staticmethod
    def _override_current_version(existing_address):
        """
        Update a previous version of an address, or override an existing one

        :param existing_address: existing EntityVersionAddress
        :return: EntityVersion or None if a new vesion must be created
        """
        today = date.today()
        last_version = existing_address.entity_version

        if last_version.start_date != today:
            # End the previous version if start_date is changed
            last_version.end_date = today - timedelta(days=1)
            last_version.save()
            # We can safely create a new version
            last_version = None
        else:
            # Latest version date is today, delete the related address (if existing)
            last_version.entityversionaddress_set.all().delete()
        return last_version

    @staticmethod
    def _is_address_unchanged(row, address):
        """
        Check if there are differences between imported address and existing

        :param row: Dict address from CSV file
        :param address: existing EntityVersionAddress or None
        :return: True if the two address are the same
        """
        return address and all([
            row[STREET_NUM] == address.street_number,
            row[STREET] == address.street,
            row[POSTAL_CODE] == address.postal_code,
            row[CITY] == address.city,
            row[COUNTRY] == address.country and address.country.name,
        ])
