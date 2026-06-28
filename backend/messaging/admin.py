from django.contrib import admin
from .models import Conversation, Message


@admin.register(Conversation)
class ConversationAdmin(admin.ModelAdmin):
    list_display = ['id', 'date_creation', 'date_dernier_message']


@admin.register(Message)
class MessageAdmin(admin.ModelAdmin):
    list_display = ['expediteur', 'conversation', 'contenu', 'lu', 'date_envoi']
    list_filter = ['lu']