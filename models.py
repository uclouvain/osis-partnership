from datetime import date, datetime

from django.conf import settings
from django.db import models
from django.db.models import Max
from django.urls import reverse
from django.utils import timezone
from django.utils.functional import cached_property
from django.utils.html import format_html
from django.utils.safestring import mark_safe
from django.utils.translation import ugettext_lazy as _

from base.models.entity import Entity
from base.models.entity_version import EntityVersion
from base.models.person import Person
from partnership.utils import user_is_adri, user_is_gf, user_is_in_user_faculty, merge_date_ranges


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
    university_offers = models.ManyToManyField(
        'base.EducationGroupYear',
        verbose_name=_('university_offers'),
        related_name='partnerships',
        blank=True,
    )
    supervisor = models.ForeignKey(
        'base.Person',
        verbose_name=_('partnership_supervisor'),
        related_name='partnerships_supervisor',
        blank=True,
        null=True,
    )

    start_date = models.DateField(_('start_date'))

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
        return self.agreements.filter(status=PartnershipAgreement.STATUS_VALIDATED).exists()

    @property
    def validated_agreements(self):
        return self.agreements.filter(status=PartnershipAgreement.STATUS_VALIDATED)

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
    def agreements_dates_ranges(self):
        ranges = self.validated_agreements.values('start_academic_year__start_date', 'end_academic_year__end_date')
        ranges = [{
            'start': range['start_academic_year__start_date'], 'end': range['end_academic_year__end_date']
        } for range in ranges]
        return merge_date_ranges(ranges)

    @cached_property
    def has_missing_valid_years(self):
        now = date.today()
        ranges = self.agreements_dates_ranges
        for range in ranges:
            if now < range['end'] and now >= range['start']:
                return False
        return True

    @cached_property
    def current_year(self):
        now = timezone.now()
        return self.years.filter(academic_year__start_date__gte=now, academic_year__end_date__lte=now).first()

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


class PartnershipYear(models.Model):
    EDUCATION_FIELD_CHOICES = (
        ('0110', _('0110 - Education, not further defined')),
        ('0111', _('0111 - Education science')),
        ('0112', _('0112 - Training for pre-school teachers')),
        ('0113', _('0113 - Teacher training without subject specialization')),
        ('0114', _('0114 - Teacher training with subject specialization')),
        ('0119', _('0119 - Education, not elsewhere classified')),
        ('0188', _('0188 - Education, inter-disciplinary programmes')),
        ('0210', _('0210 - Arts, not further defined')),
        ('0211', _('0211 - Audio-visual techniques and media production')),
        ('0212', _('0212 - Fashion, interior and industrial design')),
        ('0213', _('0213 - Fine arts')),
        ('0214', _('0214 - Handicrafts')),
        ('0215', _('0215 - Music and performing arts')),
        ('0219', _('0219 - Arts, not elsewhere classified')),
        ('0220', _('0220 - Humanities (except languages), not further defined')),
        ('0221', _('0221 - Religion and theology')),
        ('0222', _('0222 - History and archaeology')),
        ('0223', _('0223 - Philosophy and ethics')),
        ('0229', _('0229 - Humanities (except languages), not elsewhere classified')),
        ('0230', _('0230 - Languages, not further defined')),
        ('0231', _('0231 - Language acquisition')),
        ('0232', _('0232 - Literature and linguistics')),
        ('0239', _('0239 - Languages, not elsewhere classified')),
        ('0288', _('0288 - Arts and humanities, inter-disciplinary programmes')),
        ('0310', _('0310 - Social and behavioural sciences, not further defined')),
        ('0311', _('0311 - Economics')),
        ('0312', _('0312 - Political sciences and civics')),
        ('0313', _('0313 - Psychology')),
        ('0314', _('0314 - Sociology and cultural studies')),
        ('0319', _('0319 - Social and behavioural sciences, not elsewhere classified')),
        ('0320', _('0320 - Journalism and information, not further defined')),
        ('0321', _('0321 - Journalism and reporting')),
        ('0322', _('0322 - Library, information and archival studies')),
        ('0329', _('0329 - Journalism and information, not elsewhere classified')),
        ('0388', _('0388 - Social sciences, journalism and information, inter-disciplinary programmes')),
        ('0410', _('0410 - Business and administration, not further defined')),
        ('0411', _('0411 - Accounting and taxation')),
        ('0412', _('0412 - Finance, banking and insurance')),
        ('0413', _('0413 - Management and administration')),
        ('0414', _('0414 - Marketing and advertising')),
        ('0415', _('0415 - Secretarial and office work')),
        ('0416', _('0416 - Wholesale and retail sales')),
        ('0417', _('0417 - Work skills')),
        ('0419', _('0419 - Business and administration, not elsewhere classified')),
        ('0421', _('0421 - Law')),
        ('0429', _('0429 - Law, not elsewhere classified')),
        ('0488', _('0488 - Business, administration and law, inter-disciplinary programmes')),
        ('0510', _('0510 - Biological and related sciences, not further defined')),
        ('0511', _('0511 - Biology')),
        ('0512', _('0512 - Biochemistry')),
        ('0519', _('0519 - Biological and related sciences, not elsewhere classifed')),
        ('0520', _('0520 - Environment, not further defined')),
        ('0521', _('0521 - Environmental sciences')),
        ('0522', _('0522 - Natural environments and wildlife')),
        ('0529', _('0529 - Environment, not elsewhere classified')),
        ('0530', _('0530 - Physical sciences, not further defined')),
        ('0531', _('0531 - Chemistry')),
        ('0532', _('0532 - Earth sciences')),
        ('0533', _('0533 - Physics')),
        ('0539', _('0539 - Physical sciences, not elsewhere classified')),
        ('0540', _('0540 - Mathematics and statistics, not further defined')),
        ('0541', _('0541 - Mathematics')),
        ('0542', _('0542 - Statistics')),
        ('0549', _('0549 - Mathematics and statistics, not elsewhere classified')),
        ('0588', _('0588 - Natural sciences, mathematics and statistics, inter-disciplinary programmes')),
        ('0610', _('0610 - Information and Communication Technologies (ICTs), not further defined')),
        ('0611', _('0611 - Computer use')),
        ('0612', _('0612 - Database and network design and administration')),
        ('0613', _('0613 - Software and applications development and analysis')),
        ('0619', _('0619 - Information and Communication Technologies (ICTs), not elsewhere classified')),
        ('0688', _('0688 - Information and Communication Technologies (ICTs), inter-disciplinary programmes')),
        ('0710', _('0710 - Engineering and engineering trades, not further defined')),
        ('0711', _('0711 - Chemical engineering and processes')),
        ('0712', _('0712 - Environmental protection technology')),
        ('0713', _('0713 - Electricity and energy')),
        ('0714', _('0714 - Electronics and automation')),
        ('0715', _('0715 - Mechanics and metal trades')),
        ('0716', _('0716 - Motor vehicles, ships and aircraft')),
        ('0719', _('0719 - Engineering and engineering trades, not elsewhere classified')),
        ('0720', _('0720 - Manufacturing and processing, not further defined')),
        ('0721', _('0721 - Food processing')),
        ('0722', _('0722 - Materials (glass, paper, plastic and wood)')),
        ('0723', _('0723 - Textiles (clothes, footwear and leather)')),
        ('0724', _('0724 - Mining and extraction')),
        ('0729', _('0729 - Manufacturing and processing, not elsewhere classified')),
        ('0730', _('0730 - Architecture and construction, not further defined')),
        ('0731', _('0731 - Architecture and town planning')),
        ('0732', _('0732 - Building and civil engineering')),
        ('0739', _('0739 - Architecture and construction, not elsewhere classified')),
        ('0788', _('0788 - Engineering, manufacturing and construction, inter-disciplinary programmes')),
        ('0810', _('0810 - Agriculture, not further defined')),
        ('0811', _('0811 - Crop and livestock production')),
        ('0812', _('0812 - Horticulture')),
        ('0819', _('0819 - Agriculture, not elsewhere classified')),
        ('0821', _('0821 - Forestry')),
        ('0829', _('0829 - Forestry, not elsewhere classified')),
        ('0831', _('0831 - Fisheries')),
        ('0839', _('0839 - Fisheries, not elsewhere classified')),
        ('0841', _('0841 - Veterinary')),
        ('0849', _('0849 - Veterinary, not elsewhere classified')),
        ('0888', _('0888 - Agriculture, forestry, fisheries, veterinary, inter-disciplinary programmes')),
        ('0910', _('0910 - Health, not further defined')),
        ('0911', _('0911 - Dental studies')),
        ('0912', _('0912 - Medicine')),
        ('0913', _('0913 - Nursing and midwifery')),
        ('0914', _('0914 - Medical diagnostic and treatment technology')),
        ('0915', _('0915 - Therapy and rehabilitation')),
        ('0916', _('0916 - Pharmacy')),
        ('0917', _('0917 - Traditional and complementary medicine and therapy')),
        ('0919', _('0919 - Health, not elsewhere classified')),
        ('0920', _('0920 - Welfare, not further defined')),
        ('0921', _('0921 - Care of the elderly and of disabled adults')),
        ('0922', _('0922 - Child care and youth services')),
        ('0923', _('0923 - Social work and counselling')),
        ('0929', _('0929 - Welfare, not elsewhere classified')),
        ('0988', _('0988 - Health and Welfare, inter-disciplinary programmes')),
        ('1010', _('1010 - Personal services, not further defined')),
        ('1011', _('1011 - Domestic services')),
        ('1012', _('1012 - Hair and beauty services')),
        ('1013', _('1013 - Hotel, restaurants and catering')),
        ('1014', _('1014 - Sports')),
        ('1015', _('1015 - Travel, tourism and leisure')),
        ('1019', _('1019 - Personal services, not elsewhere classified')),
        ('1020', _('1020 - Hygiene and occupational health services, not further defined')),
        ('1021', _('1021 - Community sanitation')),
        ('1022', _('1022 - Occupational health and safety')),
        ('1029', _('1029 - Hygiene and occupational health services, not elsewhere classified')),
        ('1030', _('1030 - Security services, not further defined')),
        ('1031', _('1031 - Military and defence')),
        ('1032', _('1032 - Protection of persons and property')),
        ('1039', _('1039 - Security services, not elsewhere classified')),
        ('1041', _('1041 - Transport services')),
        ('1049', _('1049 - Transport services, not elsewhere classified')),
        ('1088', _('1088 - Services, inter-disciplinary programmes')),
    )
    EDUCATION_LEVEL_CHOICES = (
        ('ISCED-5', _('Short cycle within the first cycle / Short-cycle tertiary education (EQF-5)')),
        ('ISCED-6', _('First cycle / Bachelor’s or equivalent level (EQF-6)')),
        ('ISCED-7', _('Second cycle / Master’s or equivalent level (EQF-7)')),
        ('ISCED-8', _('Third cycle / Doctoral or equivalent level (EQF-8)')),
        ('ISCED-9', _('Not elsewhere classified')),
    )
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
    education_field = models.CharField(
        _('education_field'),
        max_length=255,
        choices=EDUCATION_FIELD_CHOICES,
    )
    education_level = models.CharField(
        _('education_level'),
        max_length=255,
        choices=EDUCATION_LEVEL_CHOICES,
        blank=True,
        null=True,
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
        ranges = self.partnership.agreements_dates_ranges
        for range in ranges:
            if self.academic_year.start_date >= range['start'] and self.academic_year.end_date <= range['end']:
                return True
        return False


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
        ordering = ['-start_academic_year__start_date',]

    def __str__(self):
        return '{0} > {1}'.format(self.start_academic_year, self.end_academic_year)


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
