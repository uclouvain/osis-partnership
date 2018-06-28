from django.contrib import admin

from partnership.models import Partner, Partnership, PartnerType, PartnerTag, PartnershipType, PartnershipTag, \
    PartnerEntity, Media, Contact, Address, ContactType


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


class PartnershipAdmin(admin.ModelAdmin):
    raw_id_fields = ('ucl_university', 'ucl_university_labo', 'university_offers')

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


admin.site.register(PartnerType, ValueAdmin)
admin.site.register(PartnerTag, ValueAdmin)
admin.site.register(Partner, PartnerAdmin)
admin.site.register(PartnershipType, ValueAdmin)
admin.site.register(PartnershipTag, ValueAdmin)
admin.site.register(Partnership, PartnershipAdmin)
admin.site.register(Media)
admin.site.register(ContactType)
admin.site.register(Contact)
admin.site.register(Address)
