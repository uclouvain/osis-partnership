from django.contrib import admin

from partnership.models import Partner, Partnership, PartnerType, PartnerTag, PartnershipType, PartnershipTag


class PartnerAdmin(admin.ModelAdmin):
    class Meta:
        fields = '__all__'

    def save_form(self, request, form, change):
        """
        Set the author if the partner is being created
        """
        partner = form.save(commit=False)
        if not change:
            partner.author = request.user
        return partner


class PartnershipAdmin(admin.ModelAdmin):
    class Meta:
        fields = '__all__'

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
    class Meta:
        fields = ['value']

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
