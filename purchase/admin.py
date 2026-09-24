from django.contrib import admin
from .models import Requisition, HeadOfRequisition,Notification,RequisitionComparative,ExpenseVoucher,PettyCash,ExpenseRequisition,BillRequisition,BillRequisitionApprovalPayment,RequisitionApprovalPayment,FCMDevice

admin.site.register(Requisition)
admin.site.register(HeadOfRequisition)
admin.site.register(Notification)
admin.site.register(RequisitionComparative)
admin.site.register(ExpenseVoucher)
admin.site.register(PettyCash)
admin.site.register(ExpenseRequisition)
admin.site.register(BillRequisition)
admin.site.register(BillRequisitionApprovalPayment)
admin.site.register(RequisitionApprovalPayment)
admin.site.register(FCMDevice)
