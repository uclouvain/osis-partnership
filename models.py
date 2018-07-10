from datetime import date

from django.db.models import Max
from django.utils import timezone

from base.models.entity import Entity
from base.models.person import Person
from django.conf import settings
from django.db import models
from django.urls import reverse
from django.utils.functional import cached_property
from django.utils.translation import ugettext_lazy as _
from partnership.utils import user_is_adri


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
    name = models.CharField(_('name'), max_length=255)
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
        try:
            user_is_in_author_faculty = (
                user
                .person
                .entitymanager_set
                .filter(entity__entitymanager__person__user=self.author)
                .exists()
            )
        except Person.DoesNotExist:
            user_is_in_author_faculty = False
        return user == self.author or user_is_adri(user) or user_is_in_author_faculty

    def user_can_delete(self, user):
        return self.user_can_change(user) and not self.partnerships.exists() and not self.childs.exists()


class Partner(models.Model):
    CONTACT_TYPE_CHOICES =(
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
    changed = models.DateField(_('modified'), auto_now=True, editable=False)

    is_valid = models.BooleanField(_('is_valid'), default=False)
    name = models.CharField(_('name'), max_length=255)
    is_ies = models.BooleanField(_('is_ies'), default=False)
    partner_type = models.ForeignKey(
        PartnerType,
        verbose_name=_('partner_type'),
        related_name='partners',
        on_delete=models.PROTECT,
    )
    partner_code = models.CharField(_('partner_code'), max_length=255, unique=True)
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
        try:
            is_adri = user_is_adri(user)
            is_gf = (
                user
                .person
                .entitymanager_set.all()
                .exists()
            )
            return is_adri or is_gf
        except Person.DoesNotExist:
            return False

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


class PartnershipType(models.Model):
    value = models.CharField(max_length=255, unique=True)

    class Meta:
        ordering = ('value',)

    def __str__(self):
        return self.value


class PartnershipTag(models.Model):
    value = models.CharField(max_length=255, unique=True)

    class Meta:
        ordering = ('value',)

    def __str__(self):
        return self.value


class Partnership(models.Model):
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
    )
    ucl_university_labo = models.ForeignKey(
        'base.Entity',
        verbose_name=_('ucl_university_labo'),
        on_delete=models.PROTECT,
        related_name='partnerships_labo',
        blank=True,
        null=True,
    )
    university_offers = models.ManyToManyField(
        'base.EducationGroupYear',
        verbose_name=_('university_offers'),
        related_name='partnerships',
    )

    # supervisor = ?

    start_date = models.DateField(_('start_date'), null=True, blank=True)

    contacts = models.ManyToManyField(
        'partnership.Contact',
        verbose_name=_('contacts'),
        related_name='+',
        blank=True,
    )

    # Accord Signées => TODO PartnershipAgreement

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

    @cached_property
    def is_valid(self):
        return self.agreements.filter(status=PartnershipAgreement.STATUS_VALIDATED).exists()

    @cached_property
    def end_date(self):
        validated_agreements = self.agreements.filter(status=PartnershipAgreement.STATUS_VALIDATED)
        if not validated_agreements.exists():
            return None
        return validated_agreements.aggregate(end_date=Max('end_academic_year__end_date'))['end_date']

    @cached_property
    def current_year(self):
        now = timezone.now()
        return self.years.filter(academic_year__start_date__gte=now, academic_year__end_date__lte=now).first()

    @cached_property
    def entities_acronyms(self):
        """ Get a string of the entities acronyms """
        entities = []
        parent = self.ucl_university.entityversion_set.latest('start_date').parent
        if parent is not None:
            now = timezone.now()
            entity = parent.entityversion_set.filter(start_date__gte=now, end_date__lte=now).first()
            if entity is not None:
                entities.append(entity)
        entities.append(self.ucl_university.most_recent_acronym)
        if self.ucl_university_labo is not None:
            entities.append(self.ucl_university_labo.most_recent_acronym)
        if self.university_offers.exists():
            entities.append(' - '.join(self.university_offers.values_list('acronym', flat=True)))
        return ' / '.join(entities)


class PartnershipYear(models.Model):
    MOBILITY_TYPE_CHOICES = (
        ('SMS', _('mobility_type_sms')),
        ('SMP', _('mobility_type_smp')),
        ('STA', _('mobility_type_sta')),
        ('STT', _('mobility_type_stt')),
        ('NA', _('mobility_type_na')),
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
    # domaine etudes ?
    # niveaux etude ?
    mobility_type = models.CharField(_('mobility_type'), max_length=255, choices=MOBILITY_TYPE_CHOICES)
    partnership_type = models.ForeignKey(
        PartnershipType,
        verbose_name=_('partnership_type'),
        on_delete=models.PROTECT,
        related_name='partnerships',
    )

    class Meta:
        unique_together = ('partnership', 'academic_year')
        ordering = ('academic_year__year',)

    def __str__(self):
        return _('partnership_year_{partnership}_{year}').format(partnership=self.partnership, year=self.academic_year)


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

    note = models.TextField(
        _('note'),
        blank=True,
        default='',
    )


##### FIXME Generic Model which should be moved to a more generic app

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
        if self.first_name:
            return '{0} {1} {2}'.format(self.get_title_display(), self.last_name, self.first_name)
        return '{0} {1}'.format(self.get_title_display(), self.last_name)


class Address(models.Model):
    name = models.CharField(_('name'), help_text=_('address_name_help_text'), max_length=255, blank=True, null=True)
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
        return self.name

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

    name = models.CharField(_('name'), max_length=255)
    description = models.TextField(_('description'), default='', blank=True)
    file = models.FileField(_('file'), upload_to='medias/', blank=True, null=True)
    url = models.URLField(_('url'), blank=True, null=True)
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
