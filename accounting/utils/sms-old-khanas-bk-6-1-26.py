import requests

SMS_API_URL = "http://sms.greenheritageit.com/smsapi"
API_KEY = "$2y$10$BrBPAmdKiqRR6wnPs3Sm5.w6ieYvOXCBf2gQEaI11/Rlo/6WpXKYK110"
SENDER_ID = "Khanas"
TRANSACTION_TYPE = "P"
CAMPAIGN_ID = "cmp-DlVuuS8nxA"


def send_sms(to, message):
    """
    Send SMS using Green Heritage IT API.
    Returns True if sent, False if failed.
    """
    try:
        payload = {
            "apiKey": API_KEY,
            "senderId": SENDER_ID,
            "transactionType": TRANSACTION_TYPE,
            "campaignId": CAMPAIGN_ID,
            "mobileNo": to,
            "message": message,
        }
        response = requests.get(SMS_API_URL, params=payload, timeout=10)
        response.raise_for_status()
        return True
    except requests.RequestException as e:
        print("SMS sending failed:", e)
        return False
