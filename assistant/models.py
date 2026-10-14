"""
assistant/models.py
Guarda el historial de conversaciones del chatbot, para que el usuario
pueda ver mensajes anteriores y para poder mejorar las respuestas con
el tiempo (analizando qué preguntan más los usuarios).
"""
from django.conf import settings
from django.db import models


class ChatMessage(models.Model):
    class Role(models.TextChoices):
        USER = 'user', 'Usuario'
        ASSISTANT = 'assistant', 'Asistente'

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='chat_messages')
    role = models.CharField(max_length=10, choices=Role.choices)
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Mensaje de chat'
        verbose_name_plural = 'Mensajes de chat'
        ordering = ['created_at']

    def __str__(self):
        return f'{self.user} · {self.role} · {self.content[:40]}'
