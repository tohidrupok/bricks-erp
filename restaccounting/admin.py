from django.contrib import admin
from .models import CashRestType,SalesRestType,RestLoanVoucher,RestHeadOfAccount,CreditRestVoucher,Collection,DailyPayment,RestBalanceTransfer,RestMainChequeBook,RestMainCheque,LedgerRestEntry,RestTransactionHistory,DebitRestVoucher

admin.site.register(CashRestType)
admin.site.register(SalesRestType)
admin.site.register(RestHeadOfAccount)
admin.site.register(Collection)
admin.site.register(DailyPayment)
admin.site.register(RestBalanceTransfer)
admin.site.register(RestMainChequeBook)
admin.site.register(RestMainCheque)
admin.site.register(CreditRestVoucher)
admin.site.register(DebitRestVoucher)
admin.site.register(LedgerRestEntry)
admin.site.register(RestTransactionHistory)
admin.site.register(RestLoanVoucher)