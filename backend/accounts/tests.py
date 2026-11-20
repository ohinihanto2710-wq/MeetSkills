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
