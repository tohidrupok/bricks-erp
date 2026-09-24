# purchase/utils.py
from pyfcm import FCMNotification
from django.conf import settings

def send_push_notification(title, body, tokens):
    if not tokens:
        return None
    push_service = FCMNotification(api_key=settings.FCM_SERVER_KEY)
    return push_service.notify_multiple_devices(
        registration_ids=tokens,
        message_title=title,
        message_body=body,
    )
