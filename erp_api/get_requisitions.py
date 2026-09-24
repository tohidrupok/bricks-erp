# your_app/management/commands/get_requisitions.py

import requests
from django.core.management.base import BaseCommand

class Command(BaseCommand):
    help = 'Fetch requisitions data from API and print it'

    def handle(self, *args, **kwargs):
        url = "http://127.0.0.1:8000/api/v1/requisitions/"
        headers = {
            "Authorization": "Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."  # put your token here
        }
        response = requests.get(url, headers=headers)

        if response.status_code == 200:
            data = response.json()
            self.stdout.write(self.style.SUCCESS("Requisitions data fetched successfully:"))
            # Just print data here, you can format it or save it if needed
            self.stdout.write(str(data))
        else:
            self.stdout.write(self.style.ERROR(f"Failed to get data: {response.status_code}"))
            self.stdout.write(response.text)
