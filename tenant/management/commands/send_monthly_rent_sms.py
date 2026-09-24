from django.core.management.base import BaseCommand
from tenant.models import Room
from accounting.utils.sms import send_sms
from datetime import date

class Command(BaseCommand):
    help = "Send monthly rent SMS to all active tenants"

    def handle(self, *args, **kwargs):
        month_text = date.today().strftime("%B %Y")
        rooms = Room.objects.filter(status="Active", client__isnull=False).select_related("client")

        if not rooms.exists():
            self.stdout.write("No active tenants found.")
            return

        for room in rooms:
            tenant = room.client
            if not tenant.contact:
                self.stdout.write(f"Tenant contact missing for {tenant.name}")
                continue

            rent = room.core_room_rent or 0
            water = room.water_rent or 0
            electricity = room.electricity_rent or 0
            garbage = room.garbage_rent or 0
            service = room.service_rent or 0
            parking = room.parking_cost or 0
            other = room.other_cost or 0

            total = rent + water + electricity + garbage + service + parking + other

            sms_message = (
                f"Dear Tenant,\n"
                f"Month: {month_text}\n\n"
                f"Rent: {rent:.2f}\n"
                f"Water Bill: {water:.2f}\n"
                f"Electricity Bill: {electricity:.2f}\n"
                f"Garbage Bill: {garbage:.2f}\n"
                f"Service Charge: {service:.2f}\n\n"
                f"Total Bill: {total:.2f}\n\n"
                "Please pay within the due date.\n"
                "Thank you.\n"
                "BTP Limited\n"
                "09639222203"
            )

            result = send_sms(tenant.contact, sms_message)
            self.stdout.write(f"SMS sent: {result} -> {tenant.name} ({tenant.contact})")
