from django.core.management import setup_environ
import os
import datetime
import settings

setup_environ(settings)
from django.contrib.auth.models import User
from django.core.mail import EmailMessage

now = datetime.datetime.now()
delta = datetime.timedelta(days=10)
delay = now - delta

expired_users = User.objects.filter(is_active=True, date_joined__lt=delay).exclude(is_staff=True).exclude(username__in=['admin', 'demo'])
for user in expired_users:

    email = EmailMessage('Registration expired', 'Hi %s,\n\nYour account has been disabled.\n\n'%(user.username), 'NotreDAM <%s>' % settings.EMAIL_SENDER,
        [user.email], [],
        headers = {'Reply-To': 'NotreDAM <%s>' % settings.EMAIL_SENDER})

    email.send()

    print user

    user.is_active=False
    user.save()
