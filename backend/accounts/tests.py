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


# ===== Lien de reinitialisation : domaine du frontend =====
from django.conf import settings as dj_settings

from accounts.email_backend import _contact
from meetskills.settings import _clean_domain


class CleanDomainTests(SimpleTestCase):
    def test_nettoie_les_fautes_de_saisie(self):
        for saisi in [
            'stately-meerkat-256530.netlify.app',
            'https://stately-meerkat-256530.netlify.app',
            'https://stately-meerkat-256530.netlify.app/',
            ' stately-meerkat-256530.netlify.app. ',
            '"stately-meerkat-256530.netlify.app"',
        ]:
            self.assertEqual(_clean_domain(saisi), 'stately-meerkat-256530.netlify.app', saisi)

    def test_vide(self):
        self.assertEqual(_clean_domain(None), '')

    def test_domain_et_site_name_sont_au_premier_niveau(self):
        # Djoser 2.3.x ignore DJOSER['DOMAIN'] : il lit settings.DOMAIN
        self.assertTrue(dj_settings.DOMAIN)
        self.assertEqual(dj_settings.SITE_NAME, 'MeetSkills')


class ExpediteurTolerantTests(SimpleTestCase):
    def test_formats_valides_et_mal_saisis(self):
        attendu = {'name': 'MeetSkills', 'email': 'ohinihanto2710@gmail.com'}
        for saisi in [
            'MeetSkills <ohinihanto2710@gmail.com>',
            'MeetSkills <ohinihanto2710@gmail.com>.',   # point final (cas reel)
            '"MeetSkills <ohinihanto2710@gmail.com>"',   # guillemets autour
            "'MeetSkills <ohinihanto2710@gmail.com>'",
        ]:
            self.assertEqual(_contact(saisi), attendu, saisi)

    def test_adresse_seule(self):
        self.assertEqual(_contact('ohinihanto2710@gmail.com'),
                         {'email': 'ohinihanto2710@gmail.com'})

    def test_adresse_absente_leve_une_erreur_claire(self):
        with self.assertRaises(ValueError):
            _contact('MeetSkills <>')


@override_settings(DOMAIN='stately-meerkat-256530.netlify.app', **BREVO_SETTINGS)
class LienReinitialisationTests(APITestCase):
    @mock.patch('urllib.request.urlopen')
    def test_le_lien_pointe_vers_le_frontend(self, urlopen):
        urlopen.return_value = fake_response()
        User.objects.create_user(
            email='etudiant@example.com', password='Ancien1!mdp',
            nom='A', prenom='B', universite='UAC', filiere='Info', niveau='L1')
        self.client.post('/api/auth/users/reset_password/',
                         {'email': 'etudiant@example.com'}, format='json')

        payload = json.loads(urlopen.call_args.args[0].data)
        body = payload.get('htmlContent', '') + payload.get('textContent', '')
        self.assertIn('stately-meerkat-256530.netlify.app/reinitialiser-mot-de-passe.html?uid=', body)
        self.assertNotIn('testserver/reinitialiser', body)
        self.assertIn('MeetSkills', body)
