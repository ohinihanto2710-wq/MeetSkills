"""Envoi d'e-mails via l'API HTTPS de Brevo.

Pourquoi : l'offre gratuite de Render bloque le SMTP sortant (ports 25/465/587),
ce qui faisait attendre indéfiniment l'envoi du lien de réinitialisation.
L'API de Brevo passe par HTTPS (port 443), qui n'est pas bloqué.

Aucune dépendance supplémentaire : on utilise uniquement la bibliothèque standard.
"""
import json
import logging
import urllib.error
import urllib.request
from email.utils import parseaddr

from django.conf import settings
from django.core.mail.backends.base import BaseEmailBackend

logger = logging.getLogger(__name__)

BREVO_SEND_URL = 'https://api.brevo.com/v3/smtp/email'


def _contact(address):
    name, email = parseaddr(address)
    contact = {'email': email}
    if name:
        contact['name'] = name
    return contact


class BrevoEmailBackend(BaseEmailBackend):
    def __init__(self, fail_silently=False, **kwargs):
        super().__init__(fail_silently=fail_silently, **kwargs)
        self.api_key = getattr(settings, 'BREVO_API_KEY', '')
        self.timeout = getattr(settings, 'EMAIL_TIMEOUT', None) or 10

    def send_messages(self, email_messages):
        sent = 0
        for message in email_messages:
            try:
                self._send(message)
                sent += 1
            except Exception:
                if not self.fail_silently:
                    raise
        return sent

    def _build_payload(self, message):
        payload = {
            'sender': _contact(message.from_email or settings.DEFAULT_FROM_EMAIL),
            'to': [_contact(a) for a in message.to],
            'subject': message.subject,
        }
        if message.cc:
            payload['cc'] = [_contact(a) for a in message.cc]
        if message.bcc:
            payload['bcc'] = [_contact(a) for a in message.bcc]
        if message.reply_to:
            payload['replyTo'] = _contact(message.reply_to[0])

        html = next(
            (content for content, mimetype in getattr(message, 'alternatives', [])
             if mimetype == 'text/html'),
            None,
        )
        if html:
            payload['htmlContent'] = html
            if message.body:
                payload['textContent'] = message.body
        else:
            payload['textContent'] = message.body
        return payload

    def _send(self, message):
        if not message.to:
            return
        request = urllib.request.Request(
            BREVO_SEND_URL,
            data=json.dumps(self._build_payload(message)).encode('utf-8'),
            headers={
                'api-key': self.api_key,
                'accept': 'application/json',
                'content-type': 'application/json',
            },
            method='POST',
        )
        try:
            with urllib.request.urlopen(request, timeout=self.timeout) as response:
                response.read()
        except urllib.error.HTTPError as exc:
            # Le corps de la réponse Brevo explique la cause (clé invalide,
            # expéditeur non vérifié...) : on le garde dans les logs Render.
            body = exc.read().decode('utf-8', 'replace')
            logger.error('Brevo a refusé l\'envoi (HTTP %s) : %s', exc.code, body)
            raise
        except urllib.error.URLError as exc:
            logger.error('Brevo injoignable : %s', exc.reason)
            raise
