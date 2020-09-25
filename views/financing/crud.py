from django.urls import reverse_lazy
from django.views.generic import CreateView, UpdateView, DeleteView

from osis_role.contrib.views import PermissionRequiredMixin

__all__ = [
    'FundingAddView',
    'FundingEditView',
    'FundingDeleteView',
]


class FundingViewMixin(PermissionRequiredMixin):
    fields = '__all__'
    success_url = reverse_lazy('partnerships:financings:list')
    template_name = 'partnerships/financings/funding_form.html'

    def get_queryset(self):
        return self.kwargs['model'].objects.all()

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['verbose_name'] = self.kwargs['model']._meta.verbose_name
        return context


class FundingAddView(FundingViewMixin, CreateView):
    permission_required = 'partnership.add_funding'

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['initial'] = self.request.GET
        return kwargs


class FundingEditView(FundingViewMixin, UpdateView):
    permission_required = 'partnership.change_funding'

    def get_queryset(self):
        return self.kwargs['model'].objects.all()


class FundingDeleteView(FundingViewMixin, DeleteView):
    permission_required = 'partnership.delete_funding'
    template_name = 'partnerships/financings/funding_delete.html'
