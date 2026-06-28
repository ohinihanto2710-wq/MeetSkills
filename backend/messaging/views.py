from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from .models import Conversation, Message
from .serializers import (
    ConversationSerializer, ConversationCreateSerializer, MessageSerializer
)


class ConversationViewSet(viewsets.ModelViewSet):
    permission_classes = [permissions.IsAuthenticated]

    def get_serializer_class(self):
        if self.action == 'create':
            return ConversationCreateSerializer
        return ConversationSerializer

    def get_queryset(self):
        return Conversation.objects.filter(
            participants=self.request.user
        ).order_by('-date_dernier_message')

    def get_serializer_context(self):
        context = super().get_serializer_context()
        context['request'] = self.request
        return context

    @action(detail=True, methods=['get'])
    def messages(self, request, pk=None):
        """Retourne tous les messages d'une conversation."""
        conversation = self.get_object()
        messages = conversation.messages.order_by('date_envoi')
        # Marquer les messages comme lus
        messages.exclude(expediteur=request.user).update(lu=True)
        serializer = MessageSerializer(messages, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=['post'])
    def envoyer(self, request, pk=None):
        """Envoyer un message dans une conversation."""
        conversation = self.get_object()
        contenu = request.data.get('contenu', '').strip()
        if not contenu:
            return Response(
                {'error': 'Le contenu du message ne peut pas être vide.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        message = Message.objects.create(
            conversation=conversation,
            expediteur=request.user,
            contenu=contenu
        )
        serializer = MessageSerializer(message)
        return Response(serializer.data, status=status.HTTP_201_CREATED)


class MessageViewSet(viewsets.ReadOnlyModelViewSet):
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = MessageSerializer

    def get_queryset(self):
        return Message.objects.filter(
            conversation__participants=self.request.user
        ).order_by('date_envoi')
