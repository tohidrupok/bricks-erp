import requests

SMS_API_URL = "http://bulksmsbd.net/api/smsapi"

API_KEY = "jTpwy8ILHe6sMgZg2lx9-123"
#SENDER_ID = "8809617623388"
SENDER_ID = "BRICKS Limited"
SMS_TYPE = "text"


def send_sms(to, message):
    """
    Send SMS using BulkSMSBD API.
    Returns True if sent, False if failed.
    """
    try:
        payload = {
            "api_key": API_KEY,
            "type": SMS_TYPE,
            "number": to,
            "senderid": SENDER_ID,
            "message": message,
        }

        response = requests.get(SMS_API_URL, params=payload, timeout=10)
        response.raise_for_status()

        return True

    except requests.RequestException as e:
        print("SMS sending failed:", e)
        return False
