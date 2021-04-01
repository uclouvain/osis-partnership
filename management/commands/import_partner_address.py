import argparse
import csv
import io
from collections import defaultdict
from datetime import date, timedelta

import requests
from django.conf import settings
from django.contrib.gis.geos import Point
from django.core.management import BaseCommand, CommandError
from django.core.management.base import OutputWrapper
from django.db import transaction
from django.db.models import F, Subquery, OuterRef, Q

from base.models.entity import Entity
from base.models.entity_version import EntityVersion
from base.models.entity_version_address import EntityVersionAddress
from partnership.management.commands.progress_bar import ProgressBarMixin
from partnership.models import Partner
from reference.models.country import Country

ID = "ID"
STREET_NUM = "Numero de rue"
STREET = "Adresse"
ERASMUS = "Code Erasmus"
POSTAL_CODE = "Code postal"
CITY = "Ville"
COUNTRY = "Pays"


class Command(ProgressBarMixin, BaseCommand):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Country names mapping
        self.country_names = dict(Country.objects.values_list('name', 'pk'))

        # Partner entity id mapping
        self.entity_ids = dict(Partner.objects.annotate(
            entity_id=Subquery(
                EntityVersion.objects.filter(
                    entity__organization=OuterRef('organization_id'),
                    parent__isnull=True,
                ).order_by('-start_date').values('entity_id')[:1]
            ),
        ).values_list('pk', 'entity_id'))

        # Existing partner addresses
        self.partners = self.get_existing_partner_addresses()

        # Geocoding url
        self.url = "{esb_api}/{endpoint}".format(
            esb_api=settings.ESB_API_URL,
            endpoint=settings.ESB_GEOCODING_ENDPOINT,
        )

        self.counts = defaultdict(int)
        self.delayed_io = io.StringIO()
        self.stdout_wrapper = OutputWrapper(self.delayed_io)

    def add_arguments(self, parser: argparse.ArgumentParser):
        parser.add_argument(
            'csv_file',
            type=argparse.FileType('r', encoding="utf-8-sig"),
        )

    @staticmethod
    def check_file(reader):
        expected_fields = (
            ID, ERASMUS, STREET_NUM, STREET, POSTAL_CODE, CITY, COUNTRY
        )
        try:
            assert all(field in reader.fieldnames for field in expected_fields)
        except AssertionError:
            raise CommandError(
                'Encoding must be UTF-8\n'
                'Delimiter must be ";"\n'
                'Column names must contain {}\n'
                'Headers detected : {}'.format(
                    ", ".join(expected_fields), reader.fieldnames
                )
            )

    @staticmethod
    def get_existing_partner_addresses():
        end_date_condition = (
            Q(entity_version__end_date__isnull=True)
            | Q(entity_version__end_date__gte=date.today())
        )
        queryset = EntityVersionAddress.objects.filter(
            end_date_condition,
            entity_version__entity__organization__partner__isnull=False,
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

        # Read number of lines
        total = sum(1 for _ in file) - 1
        file.seek(0)

        reader = csv.DictReader(file, delimiter=';')
        self.check_file(reader)

        for i, row in enumerate(reader, start=1):
            try:
                self.import_address(row, options)
            except AttributeError:
                self.stdout_wrapper.write(self.style.ERROR(
                    'Conflicting entity version for partner {:>4} (entity {})'.format(
                        row[ID], self.entity_ids[int(row[ID])],
                    )
                ))
                self.counts['skipped'] += 1
            self.print_progress_bar(i, total)
            self.counts['updated'] += 1

        self.print_progress_bar(total, total)
        self.delayed_io.seek(0)
        self.stdout.write(self.delayed_io.read())

        self.stdout.write(self.style.SUCCESS(
            'Updated: {}\nNot found: {}\nSkipped: {}\nWarnings: {}\nExisting: {}'.format(
                self.counts['updated'],
                self.counts['not_found'],
                self.counts['skipped'],
                self.counts['warning'],
                self.counts['existing'],
            )
        ))

    @transaction.atomic
    def import_address(self, row, options):
        # We need at least the street to update
        if not row[STREET]:
            if options['verbosity'] >= 2:
                self.stdout_wrapper.write(self.style.WARNING(
                    'Skipping partner id {}: no address'.format(row[ID])
                ))
            return

        # Country name must exist
        if row[COUNTRY] not in self.country_names:
            self.counts['skipped'] += 1
            self.stdout_wrapper.write(self.style.ERROR(
                'Skipping partner id {}: country {} does not exist'.format(
                    row[ID], row[COUNTRY],
                )
            ))
            return

        # Check that the address has changed
        existing_address = (
            self.partners[int(row[ID])] if int(row[ID]) in self.partners
            else None
        )
        if self._is_address_unchanged(row, existing_address):
            if options['verbosity'] >= 2:
                self.stdout_wrapper.write(self.style.WARNING(
                    'Skipping partner id {}: same address'.format(row[ID])
                ))
            self.counts['existing'] += 1
            return

        parts = [
            row[STREET_NUM],
            row[STREET],
            row[POSTAL_CODE],
            row[CITY],
            row[COUNTRY],
        ]
        search = ' '.join(filter(None, parts))
        response = requests.get(self.url, {'address': search}, headers={
            'Authorization': settings.ESB_AUTHORIZATION,
        })
        results = response.json()['results']
        if not results:
            self.counts['not_found'] += 1
            self.stdout_wrapper.write(self.style.ERROR(
                'Address not found for partner id {:>4} not found: {}'.format(
                    row[ID], search,
                )
            ))
            return

        if len(results) > 1:
            self.counts['warning'] += 1
            self.stdout_wrapper.write(self.style.WARNING(
                'Multiple results for partner id {}'.format(row[ID])
            ))
        location = results[0]['geometry']['location']
        if options['verbosity'] >= 2:
            self.stdout_wrapper.write(self.style.SUCCESS(
                'Address found for partner id {:>4} : {}, {}'.format(
                    row[ID], location['lat'], location['lng'],
                )
            ))

        # Handle entity version
        last_version = None
        if existing_address:
            last_version = self._override_current_version(existing_address)

        if not last_version:
            entity_id = self.entity_ids[int(row[ID])]
            entity = Entity.objects.select_related('organization').get(pk=entity_id)
            # Create a new entity version
            last_version = EntityVersion.objects.create(
                title=entity.organization.name,
                entity_id=entity_id,
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
            country_id=self.country_names[row[COUNTRY]],
            entity_version=last_version,
        )

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
            row[COUNTRY] == (address.country and address.country.name),
        ])
