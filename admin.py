from django.contrib import admin

from partnership.models import (Address, Contact, ContactType, Financing,
                                Media, Partner, PartnerEntity, Partnership,
                                PartnershipAgreement, PartnershipEntityManager,
                                PartnershipTag, PartnershipYear,
                                PartnershipYearEducationField,
                                PartnershipYearEducationLevel, PartnerTag,
                                PartnerType, UCLManagementEntity)


class PartnershipEntityManagerAdmin(admin.ModelAdmin):
    list_display = ('person', 'entity')
    search_fields = ['person__first_name', 'person__last_name', 'entity__entityversion__acronym']
    raw_id_fields = ('person', 'entity',)


class PartnerEntityAdmin(admin.TabularInline):
    model = PartnerEntity


class PartnerAdmin(admin.ModelAdmin):
    search_fields = ('name', 'partner_code', 'erasmus_code', 'pic_code')
    list_display = ('__str__', 'partner_code', 'erasmus_code', 'pic_code')
    inlines = [
        PartnerEntityAdmin,
    ]

    def save_form(self, request, form, change):
        """
        Set the author if the partner is being created
        """
        partner = form.save(commit=False)
        if not change:
            partner.author = request.user
        return partner

    def save_formset(self, request, form, formset, change):
        """
        Given an inline formset save it to the database.
        """
        if formset.model is PartnerEntity:
            entities = formset.save(commit=False)
            for entity in entities:
                if entity.pk is None:
                    entity.author = request.user
                entity.save()
        else:
            formset.save()


class PartnershipYearInline(admin.TabularInline):
    model = PartnershipYear

    def get_queryset(self, request):
        return PartnershipYear.objects.select_related('academic_year', 'partnership__partner')


class PartnershipAgreementInline(admin.TabularInline):
    model = PartnershipAgreement

    def get_queryset(self, request):
        return PartnershipAgreement.objects.select_related('partnership__partner')


class PartnershipAdmin(admin.ModelAdmin):
    raw_id_fields = ('ucl_university', 'ucl_university_labo', 'supervisor')
    inlines = (PartnershipYearInline, PartnershipAgreementInline)

    def get_queryset(self, request):
        return Partnership.objects.select_related('partner')

    def save_form(self, request, form, change):
        """
        Set the author if the partnership is being created
        """
        partnership = form.save(commit=False)
        if not change:
            partnership.author = request.user
        return partnership


class ValueAdmin(admin.ModelAdmin):

    def get_model_perms(self, request):
        """
        Return empty perms dict thus hiding the model from admin index.
        """
        return {}


class FinancingAdmin(admin.ModelAdmin):
    fields = ('name', 'url', 'countries', 'academic_year')
    search_fields = ('name', 'countries__name',)
    list_filter = ('name', 'academic_year')


admin.site.register(PartnershipEntityManager, PartnershipEntityManagerAdmin)
admin.site.register(PartnerType)
admin.site.register(PartnerTag)
admin.site.register(Partner, PartnerAdmin)
admin.site.register(PartnershipTag)
admin.site.register(PartnershipYearEducationField)
admin.site.register(PartnershipYearEducationLevel)
admin.site.register(Partnership, PartnershipAdmin)
admin.site.register(Financing, FinancingAdmin)
admin.site.register(Media)
admin.site.register(ContactType)
admin.site.register(Contact)
admin.site.register(Address)
admin.site.register(UCLManagementEntity)
admin.site.register(PartnershipYear)
