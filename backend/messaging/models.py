from django.db import models
from django.conf import settings


class Conversation(models.Model):
    """Conversation entre deux utilisateurs, généralement initiée après un match."""
    participants = models.ManyToManyField(
        settings.AUTH_USER_MODEL, related_name='conversations'
    )
    match = models.ForeignKey(
        'matching.Match', on_delete=models.SET_NULL, null=True, blank=True,
        related_name='conversations',
        help_text="Match à l'origine de la conversation, le cas échéant."
    )
    date_creation = models.DateTimeField(auto_now_add=True)
    date_dernier_message = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Conversation"
        verbose_name_plural = "Conversations"
        ordering = ['-date_dernier_message']

    def __str__(self):
        noms = ", ".join(str(u) for u in self.participants.all())
        return f"Conversation ({noms})"


class Message(models.Model):
    """Message textuel envoyé dans une conversation."""
    conversation = models.ForeignKey(
        Conversation, on_delete=models.CASCADE, related_name='messages'
    )
    expediteur = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='messages_envoyes'
    )
    contenu = models.TextField()
    lu = models.BooleanField(default=False)
    date_envoi = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Message"
        verbose_name_plural = "Messages"
        ordering = ['date_envoi']

    def __str__(self):
        return f"{self.expediteur} — {self.contenu[:30]}"

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        # Met à jour la date du dernier message sur la conversation parente
        Conversation.objects.filter(pk=self.conversation_id).update(
            date_dernier_message=self.date_envoi
        )
