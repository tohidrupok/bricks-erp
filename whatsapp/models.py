from django.db import models
from django.contrib.auth.models import User

class WhatsAppChat(models.Model):
    MESSAGE_TYPES = [
        ('public', 'Public'),
        ('private', 'Private'),
    ]
    
    DIRECTION_CHOICES = [
        ('inbound', 'Inbound (From Customer)'),
        ('outbound', 'Outbound (From ERP)'),
    ]

    customer_number = models.CharField(max_length=20)
    message_body = models.TextField(blank=True, null=True)
    whatsapp_message_id = models.CharField(max_length=255, unique=True)
    direction = models.CharField(max_length=10, choices=DIRECTION_CHOICES)
    message_type = models.CharField(max_length=10, choices=MESSAGE_TYPES, default='public')
    sender = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True) # ERP user who sent it
    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.direction} - {self.customer_number}"