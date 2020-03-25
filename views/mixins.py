from django.conf import settings
from django.core.mail import send_mail
from django.template.loader import render_to_string

from partnership.models import PartnershipConfiguration


class NotifyAdminMailMixin:
    def notify_admin_mail(self, title, template_name, context):
        to = PartnershipConfiguration.get_configuration().email_notification_to
        send_mail(
            'OSIS-Partenariats : ' + title,
            render_to_string(
                'partnerships/mails/plain_{}'.format(template_name),
                context=context,
                request=self.request,
            ),
            settings.DEFAULT_FROM_EMAIL,
            [to],
            html_message=render_to_string(
                'partnerships/mails/{}'.format(template_name),
                context=context,
                request=self.request,
            ),
        )
