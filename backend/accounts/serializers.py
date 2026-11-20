from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError as DjangoValidationError
from rest_framework import serializers
from .models import User


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = [
            'id', 'email', 'nom', 'prenom', 'telephone',
            'universite', 'filiere', 'niveau', 'bio', 'photo',
            'email_verifie', 'date_inscription',
        ]
        read_only_fields = ['id', 'email_verifie', 'date_inscription']


class UserCreateSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, min_length=8)

    class Meta:
        model = User
        fields = [
            'id', 'email', 'password', 'nom', 'prenom', 'telephone',
            'universite', 'filiere', 'niveau',
        ]

    def validate(self, attrs):
        # Applique AUTH_PASSWORD_VALIDATORS (longueur, mots de passe courants,
        # règles de robustesse...) avec l'utilisateur en cours de création
        # pour que la ressemblance avec l'e-mail/nom soit aussi contrôlée.
        password = attrs.get('password')
        user_attrs = {k: v for k, v in attrs.items() if k != 'password'}
        try:
            validate_password(password, user=User(**user_attrs))
        except DjangoValidationError as exc:
            raise serializers.ValidationError({'password': list(exc.messages)})
        return attrs

    def create(self, validated_data):
        return User.objects.create_user(**validated_data)
