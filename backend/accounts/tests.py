from django.contrib.auth.tokens import default_token_generator
from django.core.exceptions import ValidationError
from django.utils.encoding import force_bytes
from django.utils.http import urlsafe_base64_encode
from rest_framework.test import APITestCase

from .models import User
from .validators import StrongPasswordValidator


class StrongPasswordValidatorTests(APITestCase):
    def setUp(self):
        self.validator = StrongPasswordValidator()

    def test_accepts_strong_password(self):
        self.validator.validate('Abcdef1!')

    def test_rejects_each_missing_class(self):
        for pwd, code in [
            ('abcdef1!', 'password_no_upper'),
            ('ABCDEF1!', 'password_no_lower'),
            ('Abcdefg!', 'password_no_digit'),
            ('Abcdefg1', 'password_no_special'),
        ]:
            with self.assertRaises(ValidationError) as ctx:
                self.validator.validate(pwd)
            self.assertEqual([e.code for e in ctx.exception.error_list], [code])


class RegistrationPasswordPolicyTests(APITestCase):
    url = '/api/auth/users/'

    def payload(self, password):
        return {
            'email': 'etudiant@example.com', 'password': password,
            'nom': 'Dossou', 'prenom': 'Koffi',
            'universite': 'UAC', 'filiere': 'Informatique', 'niveau': 'L1',
        }

    def test_weak_password_rejected_server_side(self):
        # 8+ caractères mais sans majuscule/chiffre/spécial : passait avant
        response = self.client.post(self.url, self.payload('motdepasse'), format='json')
        self.assertEqual(response.status_code, 400)
        self.assertIn('password', response.data)
        self.assertFalse(User.objects.filter(email='etudiant@example.com').exists())

    def test_common_password_rejected(self):
        response = self.client.post(self.url, self.payload('Password1!'), format='json')
        self.assertEqual(response.status_code, 400)

    def test_strong_password_accepted(self):
        response = self.client.post(self.url, self.payload('Tr0ub4dor&3x'), format='json')
        self.assertEqual(response.status_code, 201, response.data)
        user = User.objects.get(email='etudiant@example.com')
        self.assertTrue(user.check_password('Tr0ub4dor&3x'))


class ResetPasswordPolicyTests(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            email='a@example.com', password='Ancien1!mdp',
            nom='A', prenom='B', universite='UAC', filiere='Info', niveau='L1',
        )
        self.uid = urlsafe_base64_encode(force_bytes(self.user.pk))
        self.token = default_token_generator.make_token(self.user)

    def confirm(self, password):
        return self.client.post('/api/auth/users/reset_password_confirm/', {
            'uid': self.uid, 'token': self.token, 'new_password': password,
        }, format='json')

    def test_weak_new_password_rejected(self):
        response = self.confirm('motdepasse')
        self.assertEqual(response.status_code, 400)
        self.user.refresh_from_db()
        self.assertTrue(self.user.check_password('Ancien1!mdp'))

    def test_strong_new_password_accepted(self):
        response = self.confirm('Nouveau9#mdp')
        self.assertEqual(response.status_code, 204, getattr(response, 'data', None))
        self.user.refresh_from_db()
        self.assertTrue(self.user.check_password('Nouveau9#mdp'))


# ===== Envoi d'e-mails via Brevo =====
import io
import json
import urllib.error
from unittest import mock

from django.core.mail import EmailMultiAlternatives, send_mail
from django.test import SimpleTestCase, override_settings

BREVO_SETTINGS = dict(
    EMAIL_BACKEND='accounts.email_backend.BrevoEmailBackend',
    BREVO_API_KEY='cle-de-test',
    DEFAULT_FROM_EMAIL='MeetSkills <expediteur@example.com>',
)


def fake_response():
    response = mock.MagicMock()
    response.__enter__.return_value = response
    response.read.return_value = b'{"messageId": "<abc@smtp-relay.brevo.com>"}'
    return response


@override_settings(**BREVO_SETTINGS)
class BrevoEmailBackendTests(SimpleTestCase):
    @mock.patch('urllib.request.urlopen')
    def test_envoie_la_requete_attendue(self, urlopen):
        urlopen.return_value = fake_response()
        sent = send_mail('Sujet', 'Corps du message', None, ['dest@example.com'])

        self.assertEqual(sent, 1)
        request = urlopen.call_args.args[0]
        self.assertEqual(request.full_url, 'https://api.brevo.com/v3/smtp/email')
        self.assertEqual(request.get_header('Api-key'), 'cle-de-test')
        self.assertEqual(urlopen.call_args.kwargs['timeout'], 10)
        payload = json.loads(request.data)
        self.assertEqual(payload['sender'],
                         {'name': 'MeetSkills', 'email': 'expediteur@example.com'})
        self.assertEqual(payload['to'], [{'email': 'dest@example.com'}])
        self.assertEqual(payload['subject'], 'Sujet')
        self.assertEqual(payload['textContent'], 'Corps du message')
        self.assertNotIn('htmlContent', payload)

    @mock.patch('urllib.request.urlopen')
    def test_inclut_la_version_html(self, urlopen):
        urlopen.return_value = fake_response()
        message = EmailMultiAlternatives('S', 'texte', None, ['dest@example.com'])
        message.attach_alternative('<p>html</p>', 'text/html')
        message.send()

        payload = json.loads(urlopen.call_args.args[0].data)
        self.assertEqual(payload['htmlContent'], '<p>html</p>')
        self.assertEqual(payload['textContent'], 'texte')

    @mock.patch('urllib.request.urlopen')
    def test_erreur_http_remontee(self, urlopen):
        urlopen.side_effect = urllib.error.HTTPError(
            'https://api.brevo.com/v3/smtp/email', 401, 'Unauthorized', {},
            io.BytesIO(b'{"message": "Key not found"}'))
        with self.assertLogs('accounts.email_backend', level='ERROR') as logs:
            with self.assertRaises(urllib.error.HTTPError):
                send_mail('S', 'c', None, ['dest@example.com'])
        self.assertIn('Key not found', logs.output[0])

    @mock.patch('urllib.request.urlopen')
    def test_fail_silently(self, urlopen):
        urlopen.side_effect = urllib.error.URLError('injoignable')
        with self.assertLogs('accounts.email_backend', level='ERROR'):
            sent = send_mail('S', 'c', None, ['dest@example.com'], fail_silently=True)
        self.assertEqual(sent, 0)


@override_settings(**BREVO_SETTINGS)
class ResetPasswordEmailFlowTests(APITestCase):
    """Parcours complet « mot de passe oublié » : Djoser -> backend Brevo."""

    def setUp(self):
        self.user = User.objects.create_user(
            email='etudiant@example.com', password='Ancien1!mdp',
            nom='A', prenom='B', universite='UAC', filiere='Info', niveau='L1',
        )

    @mock.patch('urllib.request.urlopen')
    def test_demande_de_reinitialisation_envoie_le_lien(self, urlopen):
        urlopen.return_value = fake_response()
        response = self.client.post(
            '/api/auth/users/reset_password/', {'email': 'etudiant@example.com'},
            format='json')

        self.assertEqual(response.status_code, 204)
        self.assertEqual(urlopen.call_count, 1)
        payload = json.loads(urlopen.call_args.args[0].data)
        self.assertEqual(payload['to'], [{'email': 'etudiant@example.com'}])
        body = payload.get('htmlContent', '') + payload.get('textContent', '')
        self.assertIn('reinitialiser-mot-de-passe.html?uid=', body)

    @mock.patch('urllib.request.urlopen')
    def test_email_inconnu_n_envoie_rien(self, urlopen):
        response = self.client.post(
            '/api/auth/users/reset_password/', {'email': 'inconnu@example.com'},
            format='json')
        self.assertEqual(response.status_code, 204)
        urlopen.assert_not_called()
