# ##############################################################################
#
#  OSIS stands for Open Student Information System. It's an application
#  designed to manage the core business of higher education institutions,
#  such as universities, faculties, institutes and professional schools.
#  The core business involves the administration of students, teachers,
#  courses, programs and so on.
#
#  Copyright (C) 2015-2023 Université catholique de Louvain (http://www.uclouvain.be)
#
#  This program is free software: you can redistribute it and/or modify
#  it under the terms of the GNU General Public License as published by
#  the Free Software Foundation, either version 3 of the License, or
#  (at your option) any later version.
#
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#
#  A copy of this license - GNU General Public License - is available
#  at the root of the source code of this program.  If not,
#  see http://www.gnu.org/licenses/.
#
# ##############################################################################

from datetime import timedelta, date
from uuid import uuid4

from django.contrib import messages
from django.db import transaction
from django.shortcuts import get_object_or_404, redirect
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from django.views.generic.edit import FormMixin

from base.models.entity import Entity
from base.models.entity_version import EntityVersion
from osis_role.contrib.views import PermissionRequiredMixin
from partnership.auth.predicates import is_linked_to_adri_entity
from partnership.forms import PartnerEntityForm, PartnerForm
from partnership.forms.partner.entity import (
    PartnerEntityContactForm,
    EntityVersionAddressForm,
    PartnerEntityAddressForm,
)
from partnership.forms.partner.partner import OrganizationForm
from partnership.models import Partner, PartnerEntity, EntityProxy
from partnership.utils import generate_unique_acronym
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
        return EntityVersionAddressForm(**kwargs)

    def get_organization_form(self):
        kwargs = {
            'prefix': 'organization',
        }
        if self.request.method in ('POST', 'PUT'):
            kwargs['data'] = self.request.POST
        if self.object is not None:
            kwargs['instance'] = self.object.organization
        kwargs['user'] = self.request.user
        return OrganizationForm(**kwargs)

    def get_context_data(self, **kwargs):
        if 'form_address' not in kwargs:
            kwargs['form_address'] = self.get_address_form()
        if 'organization_form' not in kwargs:
            kwargs['organization_form'] = self.get_organization_form()
        return super().get_context_data(**kwargs)

    @transaction.atomic
    def form_valid(self, form, form_address, organization_form):
        changed = (
                form.has_changed()
                or form_address.has_changed()
                or organization_form.has_changed()
        )

        # Save organization
        organization = organization_form.save()

        # Save related entity (there must not be another entity created when truncating)
        end_date = organization_form.cleaned_data['end_date']
        at_date = end_date if end_date and end_date < date.today() else None
        entity, created = EntityProxy.objects.only_roots(at_date).update_or_create(
            defaults=dict(
                website=organization_form.cleaned_data['website'],
            ),
            organization_id=organization.pk,
        )
        last_version = self.save_entity_version(changed, entity, organization_form)

        partner = form.save(commit=False)
        is_creation = partner.pk is None
        if is_creation:
            partner.author = self.request.user.person

        partner.organization = organization
        partner.save()
        form.save_m2m()

        # Save address
        self.save_address(last_version, form_address)

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

    @staticmethod
    def save_address(last_version, form_address):
        """ Save address """
        if form_address.instance.entity_version_id != last_version.pk:
            # Save a new address version if changed or new entity version
            form_address.instance.pk = None
        form_address.instance.entity_version_id = last_version.pk
        form_address.instance.is_main = True
        form_address.save()

    def save_entity_version(self, changed, entity, organization_form):
        """
        Save entity version if anything changed

        :param changed:
        :param entity:
        :param organization_form:
        :return:
        """
        qs = entity.entityversion_set.order_by('start_date')
        start_date = organization_form.cleaned_data['start_date']
        end_date = organization_form.cleaned_data['end_date']

        if not qs:
            # This is a partner's creation
            last_version = EntityVersion.objects.create(
                title=entity.organization.name,
                entity_id=entity.pk,
                acronym=entity.organization.prefix,
                parent=None,
                start_date=start_date,
                end_date=end_date,
            )
        elif changed:
            # This is a partner's update
            first_version = qs.first()
            last_version = qs.last()

            self._update_earliest_version(start_date, qs, first_version)

            if end_date != last_version.end_date:
                self._update_latest_version(end_date, qs, last_version)

            # Refresh version if end date is not before today
            last_version = qs.all().last()
            end_date_before_today = last_version.end_date and last_version.end_date < date.today()
            if last_version.start_date < date.today() and not end_date_before_today:
                # End the previous version if start_date is changed
                last_version.end_date = date.today() - timedelta(days=1)
                last_version.save()
                last_version = EntityVersion.objects.create(
                    title=entity.organization.name,
                    entity_id=entity.pk,
                    acronym=entity.organization.prefix,
                    parent=None,
                    start_date=date.today(),
                    end_date=end_date,
                )
        else:
            last_version = qs.last()

        return last_version

    @staticmethod
    def _update_earliest_version(start_date, qs, first_version):
        if first_version.start_date < start_date:
            # Creation date has been changed, extend
            first_version.start_date = start_date
            first_version.save()
        elif first_version.start_date > start_date:
            # Creation date has been changed, truncate
            qs.filter(end_date__lte=start_date).delete()
            first_version = qs.all().first()
            first_version.start_date = start_date
            first_version.save()

    @staticmethod
    def _update_latest_version(end_date, qs, last_version):
        if (
                # Either of dates is not set
                end_date and not last_version.end_date
                or not end_date and last_version.end_date
                # Ending date has been changed, extend
                or last_version.end_date > end_date
        ):
            last_version.end_date = end_date
            last_version.save()
        elif last_version.end_date < end_date:
            # Ending date has been changed, truncate
            qs.filter(start_date__gte=end_date).delete()
            last_version = qs.all().last()
            last_version.end_date = end_date
            last_version.save()

    def form_invalid(self, form, form_address, organization_form):
        messages.error(self.request, _('partner_error'))
        return self.render_to_response(self.get_context_data(
            form=form,
            form_address=form_address,
            organization_form=organization_form,
        ))

    def post(self, request, *args, **kwargs):
        form = self.get_form()
        form_address = self.get_address_form()
        organization_form = self.get_organization_form()
        if organization_form.is_valid() and form.is_valid() and form_address.is_valid():
            return self.form_valid(form, form_address, organization_form)
        return self.form_invalid(form, form_address, organization_form)


class PartnerEntityMixin(PermissionRequiredMixin):
    login_url = 'access_denied'

    def dispatch(self, request, *args, **kwargs):
        self.partner = get_object_or_404(Partner, pk=kwargs['partner_pk'])
        return super().dispatch(request, *args, **kwargs)

    def get_queryset(self):
        return PartnerEntity.objects.child_of(self.partner)

    def get_success_url(self):
        return self.partner.get_absolute_url()

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['partner'] = self.partner
        return context


class PartnerEntityFormMixin(PartnerEntityMixin, FormMixin):
    form_class = PartnerEntityForm
    context_object_name = 'partner_entity'
    forms = None
    object = None
    PARTNER_ENTITY_FORM = ''
    CONTACT_IN_FORM = 'contact_in'
    CONTACT_OUT_FORM = 'contact_out'
    ADDRESS_FORM = 'address'

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['partner'] = self.partner
        return kwargs

    def post(self, request, *args, **kwargs):
        """
        Handle POST requests: instantiate a form instance with the passed
        POST variables and then check if it's valid.
        """
        if kwargs.get(self.pk_url_kwarg):
            self.object = self.get_object()
        forms = self.get_forms()
        if all(map(lambda form: form.is_valid(), forms.values())):
            return self.form_valid(forms)
        else:
            return self.form_invalid(forms[self.PARTNER_ENTITY_FORM])

    def get_forms(self):
        if not self.forms:
            address = None
            if self.object:
                address = self.object.entity.most_recent_entity_version.entityversionaddress_set.first()
            self.forms = {
                self.PARTNER_ENTITY_FORM: self.get_form(),
                self.CONTACT_IN_FORM: PartnerEntityContactForm(
                    self.request.POST or None,
                    prefix=self.CONTACT_IN_FORM,
                    instance=getattr(self.object, 'contact_in', None),
                ),
                self.CONTACT_OUT_FORM: PartnerEntityContactForm(
                    self.request.POST or None,
                    prefix=self.CONTACT_OUT_FORM,
                    instance=getattr(self.object, 'contact_out', None),
                ),
                self.ADDRESS_FORM: PartnerEntityAddressForm(
                    self.request.POST or None,
                    prefix=self.ADDRESS_FORM,
                    instance=address,
                ),
            }
        return self.forms

    def get_context_data(self, **kwargs):
        kwargs.update(**self.get_forms())
        return super().get_context_data(**kwargs)

    @transaction.atomic
    def form_valid(self, forms):
        changed = any(map(lambda f: f.has_changed(), forms.values()))

        entity_form = forms[self.PARTNER_ENTITY_FORM]
        address_form = forms[self.ADDRESS_FORM]

        if not entity_form.instance.pk:
            entity_form.instance.author = self.request.user.person

        entity = self.save_entity(changed, entity_form)

        # Save partner entity
        entity_form.instance.entity = entity
        entity_form.instance.partner = self.partner
        entity_form.instance.contact_in = forms[self.CONTACT_IN_FORM].save()
        entity_form.instance.contact_out = forms[self.CONTACT_OUT_FORM].save()
        entity_form.save()

        # Save address
        if address_form.has_changed():
            self.save_address(entity.most_recent_entity_version, address_form)

        messages.success(self.request, _('partner_entity_saved'))
        return redirect(self.partner)

    def save_entity(self, changed, entity_form):
        today = timezone.now().date()
        if not entity_form.instance.pk:
            # Save a new entity and entity version
            organization = self.partner.organization
            entity = Entity.objects.create(organization_id=organization.pk)
            EntityVersion.objects.create(
                entity=entity,
                start_date=today,
                acronym=generate_unique_acronym(organization.prefix),
                parent=(
                        entity_form.cleaned_data.get('parent')  # from form
                        or organization.entity_set.first()  # default is partner
                ),
                title=entity_form.cleaned_data.get('name'),
            )
            return entity

        elif changed:
            entity_version = entity_form.instance.entity.most_recent_entity_version
            if entity_version.start_date != today:
                # End the previous entity, if started not today
                entity_version.end_date = (
                        today - timedelta(days=1)
                )
                entity_version.save()
                entity_version.pk = None
                entity_version.end_date = None
                entity_version.uuid = uuid4()

            # Save entity version with previous values
            entity_version.parent = (
                    entity_form.cleaned_data.get('parent')  # from form
                    or entity_version.parent  # default is previous
            )
            entity_version.title = entity_form.cleaned_data.get('name')
            entity_version.start_date = today
            entity_version.save()
            return entity_version.entity
        return entity_form.instance.entity

    @staticmethod
    def save_address(last_version, form_address):
        """ Save address """
        if form_address.instance.entity_version_id != last_version.pk:
            # Save a new address version if changed or new entity version
            form_address.instance.pk = None
        form_address.instance.entity_version_id = last_version.pk
        form_address.instance.is_main = True
        form_address.save()

    def form_invalid(self, form):
        messages.error(self.request, _('partner_entity_error'))
        return super().form_invalid(form)
