from datetime import datetime

from django.contrib import messages
from django.core.exceptions import ValidationError
from django.db import transaction
from django.shortcuts import get_object_or_404, redirect
from django.utils.translation import gettext_lazy as _
from django.views.generic.edit import FormMixin

from base.models.entity import Entity
from base.models.entity_version import EntityVersion
from osis_role.contrib.views import PermissionRequiredMixin
from partnership.auth.predicates import is_linked_to_adri_entity
from partnership.forms import AddressForm, PartnerEntityForm, PartnerForm
from partnership.forms.partner.partner import OrganizationForm
from partnership.models import Partner
from partnership.views.mixins import NotifyAdminMailMixin


class PartnerFormMixin(NotifyAdminMailMixin, PermissionRequiredMixin):
    form_class = PartnerForm
    context_object_name = 'partner'
    prefix = 'partner'
    login_url = 'access_denied'

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user
        return kwargs

    def get_address_form(self):
        kwargs = {
            'prefix': 'contact_address',
        }
        if self.request.method in ('POST', 'PUT'):
            kwargs['data'] = self.request.POST
        if self.object is not None:
            kwargs['instance'] = self.object.contact_address
        form = AddressForm(**kwargs)
        form.fields['name'].help_text = _('mandatory_if_not_pic_ies')
        form.fields['city'].required = True
        form.fields['country'].required = True
        return form

    def get_organization_form(self):
        kwargs = {
            'prefix': 'organization',
        }
        if self.request.method in ('POST', 'PUT'):
            kwargs['data'] = self.request.POST
        if self.object is not None:
            kwargs['instance'] = self.object.organization
        kwargs['user'] = self.request.user
        form = OrganizationForm(**kwargs)
        form.fields['name'].help_text = _('mandatory_if_not_pic_ies')
        return form

    def get_context_data(self, **kwargs):
        if 'form_address' not in kwargs:
            kwargs['form_address'] = self.get_address_form()
        if 'organization_form' not in kwargs:
            kwargs['organization_form'] = self.get_organization_form()
        return super().get_context_data(**kwargs)

    @transaction.atomic
    def form_valid(self, form, form_address, organization_form):
        # Save address
        contact_address = form_address.save()

        # Save organization
        organization = organization_form.save()

        # Save related entity
        entity, created = Entity.objects.update_or_create(
            defaults=dict(
                website=organization_form.cleaned_data['website'],
            ),
            organization_id=organization.pk,
        )

        # Save entity version
        last_version = entity.get_latest_entity_version()
        start_date = organization_form.cleaned_data['start_date']
        end_date = organization_form.cleaned_data['end_date']
        if last_version and start_date and last_version.start_date != start_date:
            last_version.end_date = start_date
            last_version.save()
            last_version = None
        elif last_version and end_date and last_version.end_date != end_date:
            last_version.end_date = start_date
            last_version.save()

        if not last_version:
            EntityVersion.objects.create(
                entity_id=entity.pk,
                parent=None,
                start_date=start_date or datetime.today(),
                end_date=end_date,
            )

        partner = form.save(commit=False)
        is_creation = partner.pk is None
        if is_creation:
            partner.author = self.request.user.person

        partner.contact_address = contact_address
        partner.organization = organization
        partner.save()
        form.save_m2m()
        messages.success(self.request, _('partner_saved'))
        if is_creation and not is_linked_to_adri_entity(self.request.user):
            self.notify_admin_mail(
                '{} - {}'.format(_('partner_created'), organization.name),
                'partner_creation.html',
                {
                    'user': self.request.user,
                    'partner': partner,
                },
            )
        return redirect(partner)

    def form_invalid(self, form, form_address, organization_form):
        messages.error(self.request, _('partner_error'))
        return self.render_to_response(self.get_context_data(
            form=form,
            form_address=form_address,
            organization_form=organization_form,
        ))

    def check_form_address(self, form, form_address):
        """ Return True if the conditional mandatory form are ok """
        if not form_address.is_valid():
            return False
        if form.cleaned_data['pic_code'] or form.cleaned_data.get('is_ies', None):
            return True
        cleaned_data = form_address.cleaned_data
        if not cleaned_data['name']:
            form_address.add_error('name', ValidationError(_('required')))
        if not cleaned_data['city']:
            form_address.add_error('city', ValidationError(_('required')))
        if not cleaned_data['country']:
            form_address.add_error('country', ValidationError(_('required')))
        return form_address.is_valid()

    def post(self, request, *args, **kwargs):
        form = self.get_form()
        form_address = self.get_address_form()
        organization_form = self.get_organization_form()
        form_valid = form.is_valid()
        form_address_valid = self.check_form_address(form, form_address)
        if organization_form.is_valid() and form_valid and form_address_valid:
            return self.form_valid(form, form_address, organization_form)
        return self.form_invalid(form, form_address, organization_form)


class PartnerEntityMixin(PermissionRequiredMixin):
    login_url = 'access_denied'

    def dispatch(self, request, *args, **kwargs):
        self.partner = get_object_or_404(Partner, pk=kwargs['partner_pk'])
        return super().dispatch(request, *args, **kwargs)

    def get_queryset(self):
        return self.partner.entities.all()

    def get_success_url(self):
        return self.partner.get_absolute_url()

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['partner'] = self.partner
        return context


class PartnerEntityFormMixin(PartnerEntityMixin, FormMixin):
    form_class = PartnerEntityForm
    context_object_name = 'partner_entity'

    def get_template_names(self):
        if self.request.is_ajax():
            return 'partnerships/includes/partner_entity_form.html'
        return self.template_name

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['partner'] = self.partner
        return kwargs

    @transaction.atomic
    def form_valid(self, form):
        entity = form.save(commit=False)
        # We need to set the partner
        #  because the one on the entity is not saved yet
        entity.partner = self.partner
        if entity.pk is None:
            entity.author = self.request.user.person
        entity.address.save()
        entity.address_id = entity.address.id
        entity.contact_in.save()
        entity.contact_in_id = entity.contact_in.id
        entity.contact_out.save()
        entity.contact_out_id = entity.contact_out.id
        entity.save()
        form.save_m2m()
        messages.success(self.request, _('partner_entity_saved'))
        return redirect(self.partner)

    def form_invalid(self, form):
        messages.error(self.request, _('partner_entity_error'))
        return super().form_invalid(form)
