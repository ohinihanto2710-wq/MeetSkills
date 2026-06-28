from rest_framework import serializers
from .models import Conversation, Message
from accounts.serializers import UserSerializer


class MessageSerializer(serializers.ModelSerializer):
    expediteur_nom = serializers.SerializerMethodField()

    class Meta:
        model = Message
        fields = [
            'id', 'conversation', 'expediteur', 'expediteur_nom',
            'contenu', 'lu', 'date_envoi',
        ]
        read_only_fields = ['expediteur', 'date_envoi', 'conversation']

    def get_expediteur_nom(self, obj):
        return f"{obj.expediteur.prenom} {obj.expediteur.nom}"


class ConversationSerializer(serializers.ModelSerializer):
    participants = UserSerializer(many=True, read_only=True)
    derniers_messages = serializers.SerializerMethodField()
    non_lus = serializers.SerializerMethodField()

    class Meta:
        model = Conversation
        fields = [
            'id', 'participants', 'match',
            'date_creation', 'date_dernier_message',
            'derniers_messages', 'non_lus',
        ]
        read_only_fields = ['date_creation', 'date_dernier_message']

    def get_derniers_messages(self, obj):
        messages = obj.messages.order_by('-date_envoi')[:5]
        return MessageSerializer(reversed(list(messages)), many=True).data

    def get_non_lus(self, obj):
        user = self.context['request'].user
        return obj.messages.filter(lu=False).exclude(expediteur=user).count()


class ConversationCreateSerializer(serializers.ModelSerializer):
    participant_id = serializers.IntegerField(write_only=True)

    class Meta:
        model = Conversation
        fields = ['id', 'participant_id', 'match']

    def create(self, validated_data):
        from accounts.models import User
        participant_id = validated_data.pop('participant_id')
        conversation = Conversation.objects.create(**validated_data)
        conversation.participants.add(
            self.context['request'].user,
            User.objects.get(id=participant_id)
        )
        return conversation