from typing import Dict

from django import forms
from django.contrib import admin
from django.contrib.postgres.fields import ArrayField
from django.utils.translation import gettext_lazy as _
from ordered_model.admin import OrderedModelAdmin

from osis_role.contrib.admin import EntityRoleModelAdmin, RoleModelAdmin
from partnership.auth.roles.partnership_manager import PartnershipEntityManager
from partnership.auth.roles.partnership_viewer import PartnershipViewer
from partnership.models import *


class TypeField(forms.CheckboxSelectMultiple):
    def format_value(self, value):
        if isinstance(value, str):
            value = value.split(',')
        return super().format_value(value)


class PartnershipEntityManagerAdmin(EntityRoleModelAdmin):
    list_display = ('person', 'entity', 'scopes')
    search_fields = ['person__first_name', 'person__last_name', 'entity__entityversion__acronym']
    raw_id_fields = ('person', 'entity',)
    formfield_overrides = {
        ArrayField: {'widget': TypeField(choices=PartnershipType.choices())}
    }

    def _build_model_from_csv_row(self, csv_row: Dict):
        partnership_manager = super()._build_model_from_csv_row(csv_row)
        partnership_manager.scopes = csv_row.get('SCOPES', 'ALL').split("|")
        return partnership_manager


class PartnershipViewerAdmin(RoleModelAdmin):
    raw_id_fields = ('person',)


class PartnerEntityAdmin(admin.ModelAdmin):
    model = PartnerEntity
    raw_id_fields = (
        'entity',
        'contact_in',
        'contact_out',
    )


class PartnerAdmin(admin.ModelAdmin):
    search_fields = (
        'organization__name',
        'organization__code',
        'erasmus_code',
        'pic_code',
    )
    list_display = ('__str__', 'organization_code', 'erasmus_code', 'pic_code')
    raw_id_fields = (
        'now_known_as',
        'medias',
        'author',
    )

    @staticmethod
    def organization_code(obj):
        return obj.organization.code

    def save_form(self, request, form, change):
        """
        Set the author if the partner is being created
        """
        partner = form.save(commit=False)
        if not change:
            partner.author = request.user.person
        return partner

    def save_formset(self, request, form, formset, change):
        """
        Given an inline formset save it to the database.
        """
        if formset.model is PartnerEntity:
            entities = formset.save(commit=False)
            for entity in entities:
                if entity.pk is None:
                    entity.author = request.user.person
                entity.save()
        else:
            formset.save()


class PartnershipYearInline(admin.TabularInline):
    model = PartnershipYear
    raw_id_fields = (
        'academic_year',
        'education_fields',
        'entities',
        'offers',
    )
    extra = 0

    def get_queryset(self, request):
        return PartnershipYear.objects.select_related('academic_year')


class PartnershipAgreementInline(admin.TabularInline):
    model = PartnershipAgreement
    raw_id_fields = (
        'media',
    )
    extra = 0


class PartnershipPartnerRelationInline(admin.TabularInline):
    model = PartnershipPartnerRelation
    raw_id_fields = ('entity', )
    extra = 0


class PartnershipAdmin(admin.ModelAdmin):
    raw_id_fields = (
        'ucl_entity',
        'supervisor',
        'contacts',
        'medias',
    )
    inlines = (
        PartnershipPartnerRelationInline,
        PartnershipYearInline,
        PartnershipAgreementInline,
    )

    def save_form(self, request, form, change):
        """
        Set the author if the partnership is being created
        """
        partnership = form.save(commit=False)
        if not change:
            partnership.author = request.user.person
        return partnership


class ValueAdmin(admin.ModelAdmin):

    def get_model_perms(self, request):
        """
        Return empty perms dict thus hiding the model from admin index.
        """
        return {}


class FinancingAdmin(admin.ModelAdmin):
    list_display = ('type', 'academic_year')
    search_fields = ('type__name', 'countries__name',)
    list_filter = ('type__name', 'academic_year')


class FundingTypeAdmin(admin.ModelAdmin):
    list_display = ('name', 'url', 'program')
    search_fields = ('name',)
    list_filter = ('program__name', 'program__source__name')


class FundingProgramAdmin(admin.ModelAdmin):
    list_display = ('name', 'source')
    search_fields = ('name',)
    list_filter = ('source__name',)


class FundingSourceAdmin(admin.ModelAdmin):
    search_fields = ('name',)


class MediaAdmin(admin.ModelAdmin):
    search_fields = ('name', 'description')
    list_filter = ('visibility', 'is_visible_in_portal')


class ContactAdmin(admin.ModelAdmin):
    search_fields = ('last_name', 'first_name', 'email')


class AddressAdmin(admin.ModelAdmin):
    raw_id_fields = ('country',)


class PartnershipYearAdmin(admin.ModelAdmin):
    raw_id_fields = (
        'partnership',
        'academic_year',
        'entities',
        'offers',
    )


class PartnershipTypeListFilter(admin.SimpleListFilter):
    title = _('partnership_type')
    parameter_name = 'type'

    def lookups(self, request, model_admin):
        return PartnershipType.choices()

    def queryset(self, request, queryset):
        if self.value():
            return queryset.filter(types__contains=[self.value()])


class PartnershipMissionAdmin(admin.ModelAdmin):
    list_display = ('code', 'label', 'type_values')
    formfield_overrides = {
        ArrayField: {'widget': TypeField(choices=PartnershipType.choices())}
    }
    list_filter = (PartnershipTypeListFilter, )

    def type_values(self, obj):
        return ", ".join(str(PartnershipType.get_value(k)) for k in obj.types)

    type_values.short_description = _('partnership_type')


class PartnershipSubtypeAdmin(OrderedModelAdmin, PartnershipMissionAdmin):
    list_display = PartnershipMissionAdmin.list_display + (
        'is_active',
        'order',
        'move_up_down_links',
    )
    readonly_fields = ['order']
    list_filter = (PartnershipTypeListFilter, 'is_active')
    ordering = ('order', )


class UCLManagementEntityAdmin(admin.ModelAdmin):
    raw_id_fields = (
        'entity',
        'academic_responsible',
        'administrative_responsible',
        'contact_in_person',
        'contact_out_person',
    )


admin.site.register(PartnershipEntityManager, PartnershipEntityManagerAdmin)
admin.site.register(PartnershipViewer, PartnershipViewerAdmin)
admin.site.register(PartnerTag)
admin.site.register(Partner, PartnerAdmin)
admin.site.register(PartnerEntity, PartnerEntityAdmin)
admin.site.register(PartnershipTag)
admin.site.register(PartnershipYearEducationLevel)
admin.site.register(Partnership, PartnershipAdmin)
admin.site.register(Financing, FinancingAdmin)
admin.site.register(FundingType, FundingTypeAdmin)
admin.site.register(FundingProgram, FundingProgramAdmin)
admin.site.register(FundingSource, FundingSourceAdmin)
admin.site.register(Media, MediaAdmin)
admin.site.register(ContactType)
admin.site.register(MediaType)
admin.site.register(Contact, ContactAdmin)
admin.site.register(UCLManagementEntity, UCLManagementEntityAdmin)
admin.site.register(PartnershipYear, PartnershipYearAdmin)
admin.site.register(PartnershipMission, PartnershipMissionAdmin)
admin.site.register(PartnershipSubtype, PartnershipSubtypeAdmin)
