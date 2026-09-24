from django.contrib import admin
from .models import Customer,CustomerLead,CustomerFollowup,Sale,CustInfoBank,BulkSMS,BulkSMSRecipient

admin.site.register(Customer)
admin.site.register(CustomerLead)
admin.site.register(CustomerFollowup)
admin.site.register(Sale)
admin.site.register(CustInfoBank)
admin.site.register(BulkSMS)
admin.site.register(BulkSMSRecipient)