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

    def create(self, validated_data):
        return User.objects.create_user(**validated_data)