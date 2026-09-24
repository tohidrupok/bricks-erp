import json
from django.http import HttpResponse, JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from django.views import View
from .models import WhatsAppChat
from django.conf import settings

@method_decorator(csrf_exempt, name='dispatch')
class WhatsAppWebhookView(View):
    
    def get(self, request, *args, **kwargs):
        """
        Meta Webhook Verification
        """
        mode = request.GET.get('hub.mode')
        token = request.GET.get('hub.verify_token')
        challenge = request.GET.get('hub.challenge')
        
        if mode == 'subscribe' and token == settings.WHATSAPP_VERIFY_TOKEN:
            return HttpResponse(challenge, status=200)
        return HttpResponse('Verification failed', status=403)

    def post(self, request, *args, **kwargs):
        """
        Receives real-time incoming WhatsApp messages
        """
        try:
            data = json.loads(request.body.decode('utf-8'))
            
            # Extract message details from Meta's complex JSON structure
            entry = data.get('entry', [])[0]
            changes = entry.get('changes', [])[0]
            value = changes.get('value', {})
            
            if 'messages' in value:
                message = value['messages'][0]
                from_number = message['from']
                msg_body = message.get('text', {}).get('body', '[Media/Unsupported Message]')
                msg_id = message['id']
                
                # Prevent duplicate processing
                if not WhatsAppChat.objects.filter(whatsapp_message_id=msg_id).exists():
                    WhatsAppChat.objects.create(
                        customer_number=from_number,
                        message_body=msg_body,
                        whatsapp_message_id=msg_id,
                        direction='inbound',
                        message_type='public' # Defaulting incoming to public chat portal
                    )
            
            return HttpResponse('EVENT_RECEIVED', status=200)
        except Exception as e:
            # In production, log this error
            return HttpResponse('Error processing webhook', status=500)
            
            
            
            
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from .models import WhatsAppChat
from .utils import send_whatsapp_message

@login_required
def whatsapp_portal(request):
    # Filter by public or private based on user selection or roles
    view_type = request.GET.get('type', 'public') 
    
    if view_type == 'private':
        # Show only private messages sent by this specific user
        chats = WhatsAppChat.objects.filter(message_type='private', sender=request.user).order_by('-timestamp')
    else:
        chats = WhatsAppChat.objects.filter(message_type='public').order_by('-timestamp')

    return render(request, 'erp/whatsapp_portal.html', {'chats': chats, 'view_type': view_type})

@login_required
def send_bulk_whatsapp(request):
    if request.method == 'POST':
        numbers_raw = request.POST.get('numbers') # Comma-separated or textarea list
        message_text = request.POST.get('message')
        msg_visibility = request.POST.get('message_type', 'public') # 'public' or 'private'
        
        # Split numbers by comma or newlines
        number_list = [num.strip() for num in numbers_raw.replace('\n', ',').split(',') if num.strip()]
        
        for number in number_list:
            response = send_whatsapp_message(number, message_text)
            
            if 'messages' in response:
                w_id = response['messages'][0]['id']
                # Save log to ERP
                WhatsAppChat.objects.create(
                    customer_number=number,
                    message_body=message_text,
                    whatsapp_message_id=w_id,
                    direction='outbound',
                    message_type=msg_visibility,
                    sender=request.user
                )
        return redirect('whatsapp_portal')
        
    return render(request, 'erp/send_bulk.html')