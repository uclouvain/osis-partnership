from datetime import date, timedelta

from django.conf import settings
from django.db import models
from django.db.models import Max, Min
from django.urls import reverse
from django.utils import timezone
from django.utils.functional import cached_property
from django.utils.html import format_html
from django.utils.safestring import mark_safe
from django.utils.translation import ugettext_lazy as _

from base.models.academic_year import AcademicYear
from base.models.education_group_year import EducationGroupYear
from base.models.entity import Entity
from base.models.entity_version import EntityVersion
from base.models.person import Person
from partnership.utils import (merge_date_ranges, user_is_adri, user_is_gf,
                               user_is_in_user_faculty)


class PartnerType(models.Model):
    value = models.CharField(max_length=255, unique=True)

    class Meta:
        ordering = ('value',)

    def __str__(self):
        return self.value


class PartnerTag(models.Model):
    value = models.CharField(max_length=255, unique=True)

    class Meta:
        ordering = ('value',)

    def __str__(self):
        return self.value


class PartnerEntity(models.Model):
    partner = models.ForeignKey(
        'partnership.Partner',
        verbose_name=_('partner'),
        on_delete=models.CASCADE,
        related_name='entities',
    )
    name = models.CharField(_('Name'), max_length=255)
    address = models.ForeignKey(
        'partnership.Address',
        verbose_name=_('address'),
        on_delete=models.SET_NULL,
        related_name='+',
        blank=True,
        null=True,
    )
    contact_in = models.ForeignKey(
        'partnership.Contact',
        verbose_name=_('contact_in'),
        on_delete=models.SET_NULL,
        related_name='+',
        blank=True,
        null=True,
    )
    contact_out = models.ForeignKey(
        'partnership.Contact',
        verbose_name=_('contact_out'),
        on_delete=models.SET_NULL,
        related_name='+',
        blank=True,
        null=True,
    )
    parent = models.ForeignKey(
        'self',
        verbose_name=_('parent_entity'),
        on_delete=models.PROTECT,
        related_name='childs',
        blank=True,
        null=True,
    )
    comment = models.TextField(_('comment'), default='', blank=True)
    created = models.DateField(_('created'), auto_now_add=True, editable=False)
    modified = models.DateField(_('modified'), auto_now=True, editable=False)
    author = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        verbose_name=_('author'),
        on_delete=models.PROTECT,
        related_name='+',
        editable=False,
    )

    class Meta:
        ordering = ('name',)

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        return '{0}#partner-entity-{1}'.format(
            reverse('partnerships:partners:detail', kwargs={'pk': self.partner_id}),
            self.id,
        )

    def user_can_change(self, user):
        return user_is_adri(user) or user_is_in_user_faculty(user, self.author)

    def user_can_delete(self, user):
        return self.user_can_change(user) and not self.partnerships.exists() and not self.childs.exists()


class Partner(models.Model):
    CONTACT_TYPE_CHOICES = (
        ('EPLUS-EDU-HEI', _('Higher education institution (tertiary level)')),
        ('EPLUS-EDU-GEN-PRE', _('School/Institute/Educational centre – General education (pre-primary level)')),
        ('EPLUS-EDU-GEN-PRI', _('School/Institute/Educational centre – General education (primary level)')),
        ('EPLUS-EDU-GEN-SEC', _('School/Institute/Educational centre – General education (secondary level)')),
        ('EPLUS-EDU-VOC-SEC', _('School/Institute/Educational centre – Vocational Training (secondary level)')),
        ('EPLUS-EDU-VOC-TER', _('School/Institute/Educational centre – Vocational Training (tertiary level)')),
        ('EPLUS-EDU-ADULT', _('School/Institute/Educational centre – Adult education')),
        ('EPLUS-BODY-PUB-NAT', _('National Public body')),
        ('EPLUS-BODY-PUB-REG', _('Regional Public body')),
        ('EPLUS-BODY-PUB-LOC', _('Local Public body')),
        ('EPLUS-ENT-SME', _('Small and medium sized enterprise')),
        ('EPLUS-ENT-LARGE', _('Large enterprise')),
        ('EPLUS-NGO', _('Non-governmental organisation/association/social enterprise')),
        ('EPLUS-FOUND', _('Foundation')),
        ('EPLUS-SOCIAL', _('Social partner or other representative of working life '
                           '(chambers of commerce, trade union, trade association)')),
        ('EPLUS-RES', _('Research Institute/Centre')),
        ('EPLUS-YOUTH-COUNCIL', _('National Youth Council')),
        ('EPLUS-ENGO', _('European NGO')),
        ('EPLUS-NET-EU', _('EU-wide network')),
        ('EPLUS-YOUTH-GROUP', _('Group of young people active in youth work')),
        ('EPLUS-EURO-GROUP-COOP', _('European grouping of territorial cooperation')),
        ('EPLUS-BODY-ACCRED', _('Accreditation, _(certification or qualification body')),
        ('EPLUS-BODY-CONS', _('Counsellzing body')),
        ('EPLUS-INTER', _('International organisation under public law')),
        ('EPLUS-SPORT-PARTIAL', _('Organisation or association representing (parts of) the sport sector')),
        ('EPLUS-SPORT-FED', _('Sport federation')),
        ('EPLUS-SPORT-LEAGUE', _('Sport league')),
        ('EPLUS-SPORT-CLUB', _('Sport club')),
        ('OTH', _('Other')),
    )

    external_id = models.CharField(
        _('external_id'),
        help_text=_('to_synchronize_with_epc'),
        max_length=255,
        unique=True,
        blank=True,
        null=True,
    )
    changed = models.DateField(_('changed'), auto_now=True, editable=False)

    is_valid = models.BooleanField(_('is_valid'), default=False)
    name = models.CharField(_('Name'), max_length=255)
    is_ies = models.BooleanField(_('is_ies'), default=False)
    partner_type = models.ForeignKey(
        PartnerType,
        verbose_name=_('partner_type'),
        related_name='partners',
        on_delete=models.PROTECT,
    )
    partner_code = models.CharField(_('partner_code'), max_length=255, unique=True, null=True, blank=True)
    pic_code = models.CharField(_('pic_code'), max_length=255, unique=True, null=True, blank=True)
    erasmus_code = models.CharField(_('erasmus_code'), max_length=255, unique=True, null=True, blank=True)
    start_date = models.DateField(_('partner_start_date'), null=True, blank=True)
    end_date = models.DateField(_('partner_end_date'), null=True, blank=True)
    now_known_as = models.ForeignKey(
        'self',
        verbose_name=_('now_known_as'),
        on_delete=models.PROTECT,
        related_name='formely_known_as',
        null=True,
        blank=True,
    )

    contact_address = models.ForeignKey(
        'partnership.Address',
        verbose_name=_('address'),
        on_delete=models.PROTECT,
        related_name='partners',
        blank=True,
        null=True,
    )
    website = models.URLField(_('website'))
    email = models.EmailField(
        _('email'),
        help_text=_('mandatory_if_not_pic_ies'),
        null=True,
        blank=True,
    )
    phone = models.CharField(
        _('phone'),
        max_length=255,
        help_text=_('mandatory_if_not_pic_ies'),
        null=True,
        blank=True,
    )
    is_nonprofit = models.NullBooleanField(_('is_nonprofit'), blank=True)
    is_public = models.NullBooleanField(_('is_public'), blank=True)
    contact_type = models.CharField(
        _('contact_type'),
        max_length=255,
        help_text=_('mandatory_if_not_pic_ies'),
        choices=CONTACT_TYPE_CHOICES,
        null=True,
        blank=True,
    )

    use_egracons = models.BooleanField(_('use_egracons'), default=False)
    comment = models.TextField(_('comment'), default='', blank=True)
    tags = models.ManyToManyField(
        PartnerTag,
        verbose_name=_('tags'),
        related_name='partners',
        blank=True,
    )

    medias = models.ManyToManyField(
        'partnership.Media',
        verbose_name=_('medias'),
        related_name='+',
        blank=True,
    )

    created = models.DateField(_('created'), auto_now_add=True, editable=False)
    author = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        verbose_name=_('author'),
        on_delete=models.PROTECT,
        related_name='+',
        editable=False,
    )

    class Meta:
        ordering = ('-created',)
        permissions = (
            ('can_access_partners', _('can_access_partners')),
        )

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        return reverse('partnerships:partners:detail', kwargs={'pk': self.pk})

    @staticmethod
    def user_can_add(user):
        return user_is_adri(user) or user_is_gf(user)

    def user_can_change(self, user):
        return user_is_adri(user)

    @property
    def is_actif(self):
        """ Partner is not actif if it has date and is not within those. """
        if self.start_date is not None and date.today() < self.start_date:
            return False
        if self.end_date is not None and date.today() > self.end_date:
            return False
        return True

    @property
    def agreements(self):
        return (
            PartnershipAgreement.objects
            .select_related('partnership', 'start_academic_year', 'end_academic_year')
            .filter(partnership__partner=self)
        )


class PartnershipTag(models.Model):
    value = models.CharField(max_length=255, unique=True)

    class Meta:
        ordering = ('value',)

    def __str__(self):
        return self.value


class Partnership(models.Model):
    external_id = models.CharField(
        _('external_id'),
        help_text=_('to_synchronize_with_epc'),
        max_length=255,
        unique=True,
        blank=True,
        null=True,
    )

    partner = models.ForeignKey(
        Partner,
        verbose_name=_('partner'),
        on_delete=models.PROTECT,
        related_name='partnerships',
    )
    partner_entity = models.ForeignKey(
        PartnerEntity,
        verbose_name=_('partner_entity'),
        on_delete=models.PROTECT,
        related_name='partnerships',
        blank=True,
        null=True,
    )
    ucl_university = models.ForeignKey(
        'base.Entity',
        verbose_name=_('ucl_university'),
        on_delete=models.PROTECT,
        related_name='partnerships',
        limit_choices_to={'entityversion__entity_type': "FACULTY"},
    )
    ucl_university_labo = models.ForeignKey(
        'base.Entity',
        verbose_name=_('ucl_university_labo'),
        on_delete=models.PROTECT,
        related_name='partnerships_labo',
        blank=True,
        null=True,
    )
    supervisor = models.ForeignKey(
        'base.Person',
        verbose_name=_('partnership_supervisor'),
        related_name='partnerships_supervisor',
        blank=True,
        null=True,
    )

    contacts = models.ManyToManyField(
        'partnership.Contact',
        verbose_name=_('contacts'),
        related_name='+',
        blank=True,
    )

    comment = models.TextField(_('comment'), default='', blank=True)
    tags = models.ManyToManyField(
        PartnershipTag,
        verbose_name=_('tags'),
        related_name='partnerships',
        blank=True,
    )

    created = models.DateField(_('created'), auto_now_add=True, editable=False)
    modified = models.DateField(_('modified'), auto_now=True, editable=False)
    author = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        verbose_name=_('author'),
        on_delete=models.PROTECT,
        related_name='+',
        editable=False,
    )

    class Meta:
        ordering = ('-created',)
        permissions = (
            ('can_access_partners', _('can_access_partnerships')),
        )

    def __str__(self):
        return _('partnership_with_{partner}').format(partner=self.partner)

    def get_absolute_url(self):
        return reverse('partnerships:detail', kwargs={'pk': self.pk})

    @staticmethod
    def user_can_add(user):
        return user_is_adri(user) or user_is_gf(user)

    def user_can_change(self, user):
        if user_is_adri(user):
            return True
        if not user_is_in_user_faculty(user, self.author):
            return False
        # GF User can update if before year N and the day/month specified in the configuration.
        today = date.today()
        configuration = PartnershipConfiguration.get_configuration()
        min_date = date(
            today.year,
            configuration.partnership_update_max_date_month,
            configuration.partnership_update_max_date_day
        )
        return self.start_date > min_date

    @cached_property
    def is_valid(self):
        return self.validated_agreements.exists()

    @property
    def validated_agreements(self):
        return self.agreements.filter(status=PartnershipAgreement.STATUS_VALIDATED)

    @cached_property
    def start_academic_year(self):
        partnership_year = self.years.order_by('academic_year__year').first()
        if partnership_year is None:
            return None
        return partnership_year.academic_year

    @cached_property
    def end_academic_year(self):
        partnership_year = self.years.order_by('academic_year__year').last()
        if partnership_year is None:
            return None
        return partnership_year.academic_year

    @cached_property
    def start_date(self):
        return self.years.aggregate(start_date=Min('academic_year__start_date'))['start_date']

    @cached_property
    def end_date(self):
        if not self.validated_agreements.exists():
            return None
        return self.validated_agreements.aggregate(end_date=Max('end_academic_year__end_date'))['end_date']

    @cached_property
    def validity_end(self):
        agreement = (
            self.validated_agreements
                .select_related('end_academic_year')
                .order_by('-end_academic_year__end_date')
                .first()
        )
        if agreement is None:
            return None
        return agreement.end_academic_year

    @cached_property
    def valid_agreements_dates_ranges(self):
        ranges = self.validated_agreements.values('start_academic_year__start_date', 'end_academic_year__end_date')
        ranges = [{
            'start': range['start_academic_year__start_date'], 'end': range['end_academic_year__end_date']
        } for range in ranges]
        return merge_date_ranges(ranges)

    @cached_property
    def has_missing_years(self):
        """ Test if we have PartnershipYear for all of the partnership duration """
        if self.end_date is None:
            return False
        years = self.years.values_list('academic_year__start_date', flat=True).order_by('academic_year__start_date')
        ranges = [{'start': year, 'end': year + timedelta(days=366)} for year in years]
        ranges = merge_date_ranges(ranges)
        return (
            len(ranges) != 1
            or self.start_date.year < ranges[0]['start'].year
            or self.end_date.year > ranges[-1]['end'].year + 1
        )

    @cached_property
    def has_missing_valid_years(self):
        """ Test if we have valid agreements for all of the partnership duration """
        if self.end_date is None:
            return False
        ranges = self.valid_agreements_dates_ranges
        return (
            len(ranges) > 1
            or self.start_date.year < ranges[0]['start'].year
            or self.end_date.year > ranges[-1]['end'].year + 1
        )

    @cached_property
    def current_year(self):
        now = timezone.now()
        return (
            self.years
                .filter(academic_year__start_date__lte=now, academic_year__end_date__gte=now)
                .prefetch_related('education_fields', 'education_levels')
                .first()
        )

    @property
    def university_offers(self):
        if self.current_year is None:
            return EducationGroupYear.objects.none()
        return self.current_year.offers

    @cached_property
    def entities_acronyms(self):
        """ Get a string of the entities acronyms with tooltips with the title """
        entities = []
        university = self.ucl_university.entityversion_set.latest('start_date')
        if university.parent is not None:
            parent = university.parent.entityversion_set.latest('start_date')
            if parent is not None:
                entities.append(parent)
        entities.append(university)
        if self.ucl_university_labo is not None:
            labo = self.ucl_university_labo.entityversion_set.latest('start_date')
            entities.append(labo)
        if self.university_offers.exists():
            entities += list(self.university_offers.select_related('academic_year'))

        def add_tooltip(entity):
            if isinstance(entity, EntityVersion):
                entity_string = entity.acronym
            else:
                entity_string = str(entity)
            return format_html(
                '<abbr title="{0}">{1}</abbr>',
                entity.title,
                entity_string,
            )

        return mark_safe(' / '.join(map(add_tooltip, entities)))


class PartnershipYearEducationField(models.Model):
    code = models.CharField(max_length=30, unique=True)
    label = models.CharField(max_length=255)

    class Meta:
        ordering = ('code',)

    def __str__(self):
        return '{0} - {1}'.format(self.code, self.label)


class PartnershipYearEducationLevel(models.Model):
    code = models.CharField(max_length=30, unique=True)
    label = models.CharField(max_length=255)

    class Meta:
        ordering = ('code',)

    def __str__(self):
        return '{0} - {1}'.format(self.code, self.label)


class PartnershipYear(models.Model):
    TYPE_MOBILITY = 'mobility'
    TYPE_CHOICES = (
        ('intention', _('Déclaration d’intention')),
        ('cadre', _('Accord-cadre')),
        ('specifique', _('Accord spécifique')),
        ('codiplomation', _('Accord de co-diplômation')),
        ('cotutelle', _('Accord de co-tutelle')),
        (TYPE_MOBILITY, _('Partenariat de mobilité')),
        ('fond_appuie', _('Projet Fonds d’appuie à l’internationnalisation')),
        ('autre', _('Autre')),
    )

    partnership = models.ForeignKey(
        Partnership,
        verbose_name=_('partnership'),
        on_delete=models.PROTECT,
        related_name='years',
    )
    academic_year = models.ForeignKey(
        'base.AcademicYear',
        verbose_name=_('academic_year'),
        on_delete=models.PROTECT,
        related_name='+',
    )
    education_fields = models.ManyToManyField(
        PartnershipYearEducationField,
        verbose_name=_('partnership_year_education_fields'),
        blank=False,
    )
    education_levels = models.ManyToManyField(
        PartnershipYearEducationLevel,
        verbose_name=_('partnership_year_education_levels'),
        blank=True,
    )
    entities = models.ManyToManyField(
        'base.Entity',
        verbose_name=_('partnership_year_entities'),
        related_name='+',
        blank=True,
    )
    offers = models.ManyToManyField(
        'base.EducationGroupYear',
        verbose_name=_('partnership_year_offers'),
        related_name='partnerships',
        blank=True,
    )
    is_sms = models.BooleanField(_('is_sms'), default=False, blank=True)
    is_smp = models.BooleanField(_('is_smp'), default=False, blank=True)
    is_sta = models.BooleanField(_('is_sta'), default=False, blank=True)
    is_stt = models.BooleanField(_('is_stt'), default=False, blank=True)
    partnership_type = models.CharField(
        _('partnership_type'),
        max_length=255,
        choices=TYPE_CHOICES,
    )

    class Meta:
        unique_together = ('partnership', 'academic_year')
        ordering = ('academic_year__year',)
        verbose_name = _('partnership_year')

    def __str__(self):
        return _('partnership_year_{partnership}_{year}').format(partnership=self.partnership, year=self.academic_year)

    @cached_property
    def is_valid(self):
        ranges = self.partnership.valid_agreements_dates_ranges
        for range in ranges:
            if self.academic_year.start_date >= range['start'] and self.academic_year.end_date <= range['end']:
                return True
        return False

    @cached_property
    def planned_activity(self):
        activities = []
        if self.is_sms:
            activities.append('SMS')
        if self.is_smp:
            activities.append('SMP')
        if self.is_sta:
            activities.append('STA')
        if self.is_stt:
            activities.append('STT')
        return ', '.join(activities)


class PartnershipAgreement(models.Model):

    STATUS_WAITING = 'waiting'
    STATUS_VALIDATED = 'validated'
    STATUS_REFUSED = 'refused'
    STATUS_CHOICES = (
        (STATUS_WAITING, _('status_waiting')),
        (STATUS_VALIDATED, _('status_validated')),
        (STATUS_REFUSED, _('status_refused')),
    )

    partnership = models.ForeignKey(
        Partnership,
        verbose_name=_('partnership'),
        on_delete=models.PROTECT,
        related_name='agreements',
    )

    start_academic_year = models.ForeignKey(
        'base.AcademicYear',
        verbose_name=_('start_academic_year'),
        on_delete=models.PROTECT,
        related_name='+',
    )

    end_academic_year = models.ForeignKey(
        'base.AcademicYear',
        verbose_name=_('end_academic_year'),
        on_delete=models.PROTECT,
        related_name='+',
    )

    media = models.ForeignKey(
        'partnership.Media',
        verbose_name=_('media'),
        on_delete=models.PROTECT,
        related_name='+',
    )

    status = models.CharField(
        _('status'),
        max_length=10,
        choices=STATUS_CHOICES,
        default=STATUS_WAITING,
    )

    eligible = models.BooleanField(
        _('eligible'),
        default=False,
        blank=True,
    )

    comment = models.TextField(
        _('comment'),
        blank=True,
        default='',
    )

    class Meta:
        verbose_name = _('financing')
        ordering = [
            '-start_academic_year__start_date',
        ]

    def __str__(self):
        return '{0} > {1}'.format(self.start_academic_year, self.end_academic_year)

    @property
    def is_valid(self):
        return self.status == self.STATUS_VALIDATED

    def get_financings(self):
        if not self.eligible:
            return Financing.objects.none()
        country = self.partnership.partner.contact_address.country
        if country is None:
            return Financing.objects.none()
        return (
            Financing.objects
            .select_related('academic_year')
            .filter(
                countries=country,
                academic_year__year__gte=self.start_academic_year.year,
                academic_year__year__lte=self.end_academic_year.year,
            ).order_by('academic_year__year')
        )


class PartnershipConfiguration(models.Model):
    DAYS_CHOICES = [(day, day) for day in range(1, 32)]
    MONTHES_CHOICES = (
        (1, _('january')),
        (2, _('february')),
        (3, _('march')),
        (4, _('april')),
        (5, _('may')),
        (6, _('june')),
        (7, _('july')),
        (8, _('august')),
        (9, _('september')),
        (10, _('october')),
        (11, _('november')),
        (12, _('december')),
    )

    partnership_creation_max_date_day = models.IntegerField(
        _('partnership_creation_max_date_day'),
        choices=DAYS_CHOICES,
        default=31,
    )

    partnership_creation_max_date_month = models.IntegerField(
        _('partnership_creation_max_date_month'),
        choices=MONTHES_CHOICES,
        default=12,
    )

    partnership_update_max_date_day = models.IntegerField(
        _('partnership_update_max_date_day'),
        choices=DAYS_CHOICES,
        default=1,
    )

    partnership_update_max_date_month = models.IntegerField(
        _('partnership_update_max_date_month'),
        choices=MONTHES_CHOICES,
        default=3,
    )

    @staticmethod
    def get_configuration():
        try:
            return PartnershipConfiguration.objects.get()
        except PartnershipConfiguration.DoesNotExist:
            return PartnershipConfiguration.objects.create()

    def get_current_academic_year_for_creation(self):
        limit_date = date(
            date.today().year,
            self.partnership_creation_max_date_month,
            self.partnership_creation_max_date_day,
        )
        if date.today() < limit_date:
            return AcademicYear.objects.filter(year=date.today().year + 1).first()
        else:
            return AcademicYear.objects.filter(year=date.today().year + 2).first()

    def get_current_academic_year_for_modification(self):
        limit_date = date(
            date.today().year,
            self.partnership_update_max_date_month,
            self.partnership_update_max_date_day,
        )
        if date.today() < limit_date:
            return AcademicYear.objects.filter(year=date.today().year).first()
        else:
            return AcademicYear.objects.filter(year=date.today().year + 1).first()


##### FIXME Generic Model which should be moved to a more generic app


class Financing(models.Model):
    name = models.CharField(_('Name'), max_length=50)
    url = models.URLField(_('url'))
    countries = models.ManyToManyField('reference.Country', verbose_name=_('countries'))
    academic_year = models.ForeignKey('base.AcademicYear', verbose_name=_('academic_year'))

    class Meta:
        ordering = ('academic_year__year',)

    def __str__(self):
        return '{0} - {1}'.format(self.academic_year, self.name)


class ContactType(models.Model):
    value = models.CharField(max_length=255, unique=True)

    class Meta:
        ordering = ('value',)

    def __str__(self):
        return self.value


class Contact(models.Model):
    TITLE_MISTER = 'mr'
    TITLE_CHOICES = (
        (TITLE_MISTER, _('mister')),
        ('mme', _('madame')),
    )

    type = models.ForeignKey(
        ContactType,
        verbose_name=_('contact_type'),
        on_delete=models.PROTECT,
        related_name='+',
        blank=True,
        null=True,
    )
    title = models.CharField(
        _('contact_title'),
        max_length=50,
        choices=TITLE_CHOICES,
        null=True,
        blank=True,
    )
    last_name = models.CharField(_('last_name'), max_length=255, blank=True, null=True)
    first_name = models.CharField(_('first_name'), max_length=255, blank=True, null=True)
    society = models.CharField(_('society'), max_length=255, blank=True, null=True)
    function = models.CharField(_('function'), max_length=255, blank=True, null=True)
    phone = models.CharField(_('phone'), max_length=255, blank=True, null=True)
    mobile_phone = models.CharField(_('mobile_phone'), max_length=255, blank=True, null=True)
    fax = models.CharField(_('fax'), max_length=255, blank=True, null=True)
    email = models.EmailField(_('email'), blank=True, null=True)
    comment = models.TextField(_('comment'), default='', blank=True)

    def __str__(self):
        chunks = []
        if self.title is not None:
            chunks.append(self.get_title_display())
        if self.last_name:
            chunks.append(self.last_name)
        if self.first_name:
            chunks.append(self.first_name)
        return ' '.join(chunks)

    @property
    def is_empty(self):
        return not any([
            self.type,
            self.title,
            self.last_name,
            self.first_name,
            self.society,
            self.function,
            self.phone,
            self.mobile_phone,
            self.fax,
            self.email,
            self.comment,
        ])


class Address(models.Model):
    name = models.CharField(_('Name'), help_text=_('address_name_help_text'), max_length=255, blank=True, null=True)
    address = models.TextField(_('address'), default='', blank=True)
    postal_code = models.CharField(_('postal_code'), max_length=20, blank=True, null=True)
    city = models.CharField(_('city'), max_length=255, blank=True, null=True)
    city_french = models.CharField(_('city_french'), max_length=255, blank=True, null=True)
    city_english = models.CharField(_('city_english'), max_length=255, blank=True, null=True)
    country = models.ForeignKey(
        'reference.Country',
        verbose_name=_('country'),
        on_delete=models.PROTECT,
        blank=True,
        null=True,
    )

    def __str__(self):
        return self.one_line_display()

    def one_line_display(self):
        components = []
        if self.name:
            components.append(self.name)
        if self.address:
            components.append(self.address)
        if self.postal_code:
            components.append(self.postal_code)
        if self.city:
            components.append(self.city)
        if self.country:
            components.append(str(self.country).upper())
        return ', '.join(components)


class Media(models.Model):
    VISIBILITY_PUBLIC = 'public'
    VISIBILITY_STAFF = 'staff'
    VISIBILITY_STAFF_STUDENT = 'staff_student'
    VISIBILITY_CHOICES = (
        (VISIBILITY_PUBLIC, _('visibility_public')),
        (VISIBILITY_STAFF, _('visibility_staff')),
        (VISIBILITY_STAFF_STUDENT, _('visibility_staff_student')),
    )

    name = models.CharField(_('Name'), max_length=255)
    description = models.TextField(_('description'), default='', blank=True)
    file = models.FileField(_('file'), help_text=_('media_file_or_url'), upload_to='medias/', blank=True, null=True)
    url = models.URLField(_('url'), help_text=_('media_file_or_url'), blank=True, null=True)
    visibility = models.CharField(
        _('visibility'),
        max_length=50,
        choices=VISIBILITY_CHOICES,
    )
    author = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        verbose_name=_('author'),
        on_delete=models.PROTECT,
        related_name='+',
        editable=False,
    )

    def __str__(self):
        return self.name

    def get_document_file_type(self):
        return self.file.name.split('.')[-1]

    def get_document_file_size(self):
        return self.file.size
