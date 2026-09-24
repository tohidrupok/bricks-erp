from django.urls import path
from .views import WhatsAppWebhookView, whatsapp_portal, send_bulk_whatsapp

app_name = 'whatsapp'

urlpatterns = [
    path('whatsapp/webhook/', WhatsAppWebhookView.as_view(), name='whatsapp_webhook'),
    path('erp/whatsapp/', whatsapp_portal, name='whatsapp_portal'),
    path('erp/whatsapp/send-bulk/', send_bulk_whatsapp, name='send_bulk_whatsapp'),
]