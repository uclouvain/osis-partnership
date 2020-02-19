from django.conf import settings
from django.contrib import messages
from django.core.exceptions import ValidationError
from django.core.mail import send_mail
from django.db import transaction
from django.db.models import Count, Q
from django.db.models.functions import Now
from django.shortcuts import get_object_or_404, redirect
from django.template.loader import render_to_string
from django.utils.translation import gettext_lazy as _
from django.views.generic.edit import FormMixin
from django.views.generic.list import MultipleObjectMixin

from partnership.forms import AddressForm, PartnerEntityForm, PartnerFilterForm
from partnership.models import Partner, PartnershipConfiguration
from partnership.utils import user_is_adri


class PartnersListFilterMixin(FormMixin, MultipleObjectMixin):
    form_class = PartnerFilterForm
    login_url = 'access_denied'

    def get_form_kwargs(self):
        kwargs = super(PartnersListFilterMixin, self).get_form_kwargs()
        if self.request.GET:
            kwargs['data'] = self.request.GET
        return kwargs

    def filter_queryset(self, queryset):
        form = self.get_form()
        if form.is_valid():
            data = form.cleaned_data
            if data['name']:
                queryset = queryset.filter(name__icontains=data['name'])
            if data['partner_type']:
                queryset = queryset.filter(partner_type=data['partner_type'])
            if data['pic_code']:
                queryset = queryset.filter(pic_code__icontains=data['pic_code'])
            if data['erasmus_code']:
                queryset = queryset.filter(erasmus_code__icontains=data['erasmus_code'])
            if data['city']:
                queryset = queryset.filter(contact_address__city__icontains=data['city'])
            if data['country']:
                queryset = queryset.filter(contact_address__country=data['country'])
            if data['continent']:
                queryset = queryset.filter(contact_address__country__continent=data['continent'])
            if data['is_ies'] is not None:
                queryset = queryset.filter(is_ies=data['is_ies'])
            if data['is_valid'] is not None:
                queryset = queryset.filter(is_valid=data['is_valid'])
            if data['is_actif'] is not None:
                if data['is_actif']:
                    queryset = queryset.filter(
                        (Q(start_date__isnull=True) & Q(end_date__isnull=True))
                        | (Q(start_date__lte=Now()) & Q(end_date__gte=Now()))
                    )
                else:
                    queryset = queryset.filter(Q(start_date__gt=Now()) | Q(end_date__lt=Now()))
            if data['tags']:
                queryset = queryset.filter(tags__in=data['tags'])
        return queryset

    def get_ordering(self):
        return self.request.GET.get('ordering', '-created')

    def get_queryset(self):
        queryset = (
            Partner.objects.all()
            .select_related('partner_type', 'contact_address__country')
            .annotate(partnerships_count=Count('partnerships'))
        )
        queryset = self.filter_queryset(queryset)
        ordering = self.get_ordering()
        if ordering:
            queryset = queryset.order_by(ordering)
        return queryset.distinct()


class PartnerFormMixin(object):
    def get_form_kwargs(self):
        kwargs = super(PartnerFormMixin, self).get_form_kwargs()
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

    def get_context_data(self, **kwargs):
        if 'form_address' not in kwargs:
            kwargs['form_address'] = self.get_address_form()
        kwargs['user_is_adri'] = user_is_adri(self.request.user)
        return super(PartnerFormMixin, self).get_context_data(**kwargs)

    @transaction.atomic
    def form_valid(self, form, form_address):
        contact_address = form_address.save()
        partner = form.save(commit=False)
        is_create = partner.pk is None
        if is_create:
            partner.author = self.request.user
        partner.contact_address = contact_address
        partner.save()
        form.save_m2m()
        messages.success(self.request, _('partner_saved'))
        if is_create and not user_is_adri(self.request.user):
            send_mail(
                'OSIS-Partenariats : {} - {}'.format(_('partner_created'), partner.name),
                render_to_string(
                    'partnerships/mails/plain_partner_creation.html',
                    context={
                        'user': self.request.user,
                        'partner': partner,
                    },
                    request=self.request,
                ),
                settings.DEFAULT_FROM_EMAIL,
                [PartnershipConfiguration.get_configuration().email_notification_to],
                html_message=render_to_string(
                    'partnerships/mails/partner_creation.html',
                    context={
                        'user': self.request.user,
                        'partner': partner,
                    },
                    request=self.request,
                ),
            )
        return redirect(partner)

    def form_invalid(self, form, form_address):
        messages.error(self.request, _('partner_error'))
        return self.render_to_response(self.get_context_data(
            form=form,
            form_address=form_address
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
        form_valid = form.is_valid()
        form_address_valid = self.check_form_address(form, form_address)
        if form_valid and form_address_valid:
            return self.form_valid(form, form_address)
        else:
            return self.form_invalid(form, form_address)


class PartnerEntityMixin(object):
    def dispatch(self, request, *args, **kwargs):
        self.partner = get_object_or_404(Partner, pk=kwargs['partner_pk'])
        return super(PartnerEntityMixin, self).dispatch(request, *args, **kwargs)

    def get_queryset(self):
        return self.partner.entities.all()

    def get_success_url(self):
        return self.partner.get_absolute_url()

    def get_context_data(self, **kwargs):
        context = super(PartnerEntityMixin, self).get_context_data(**kwargs)
        context['partner'] = self.partner
        return context


class PartnerEntityFormMixin(PartnerEntityMixin, FormMixin):
    form_class = PartnerEntityForm

    def get_template_names(self):
        if self.request.is_ajax():
            return 'partnerships/includes/partner_entity_form.html'
        return self.template_name

    def get_form_kwargs(self):
        kwargs = super(PartnerEntityFormMixin, self).get_form_kwargs()
        kwargs['partner'] = self.partner
        return kwargs

    @transaction.atomic
    def form_valid(self, form):
        entity = form.save(commit=False)
        # We need to set the partner
        #  because the one on the entity is not saved yet
        entity.partner = self.partner
        if entity.pk is None:
            entity.author = self.request.user
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
        return super(PartnerEntityFormMixin, self).form_invalid(form)
