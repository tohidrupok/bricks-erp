from django.contrib import admin
from .models import RestaurantCategory,RestaurantItem,RestaurantExpenseCategory,RestRequisition,RestInventories,RestaurantKitchenLedger,RestInventoryUse,RestaurantCustomer,RestaurantItemAmount,RestaurantSale,RestaurantSaleItem,RestHeadofAcct,RestaurantAccount,RestaurantSupplier,RestExpenseRequisition,RestRequisitionApprovalHistory

admin.site.register(RestaurantCategory)
admin.site.register(RestaurantItem)
admin.site.register(RestaurantCustomer)
admin.site.register(RestaurantItemAmount)
admin.site.register(RestaurantSale)
admin.site.register(RestaurantSaleItem)
admin.site.register(RestHeadofAcct)
admin.site.register(RestaurantAccount)
admin.site.register(RestaurantSupplier)
admin.site.register(RestExpenseRequisition)
admin.site.register(RestRequisition)
admin.site.register(RestInventories)
admin.site.register(RestInventoryUse)
admin.site.register(RestRequisitionApprovalHistory)
admin.site.register(RestaurantKitchenLedger)
admin.site.register(RestaurantExpenseCategory)
