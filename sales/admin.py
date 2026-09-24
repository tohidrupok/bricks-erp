from django.contrib import admin
from .models import Sales,FlatPlot,PropertyFlatPlot,PropertySales,InstallmentPayment,SharePlot,SharePerson,ShareInstallmentPayment

admin.site.register(Sales)
admin.site.register(FlatPlot)
admin.site.register(PropertyFlatPlot)
admin.site.register(PropertySales)
admin.site.register(InstallmentPayment)
admin.site.register(SharePlot)
admin.site.register(SharePerson)
admin.site.register(ShareInstallmentPayment)