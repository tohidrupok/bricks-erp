from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import RequisitionViewSet,InventoriesViewSet,DebitVoucherViewSet,CreditVoucherViewSet,LedgerEntryViewSet,NotificationViewSet,ProjectBOQViewSet,TransactionLedgerViewSet,CustomerViewSet,RoomViewSet,ActiveRoomViewSet,DeactiveRoomViewSet,BillViewSet,RentViewSet,ReceiveVoucherViewSet,PaymentVoucherViewSet,LedgerEntryCustomViewSet,LedgerEntryCustomtrailViewSet,HeadOfAccountViewSet,CashTypeViewSet,ProjectFirstLevelNameViewSet,SuppliersViewSet,SiteSupervisorViewSet
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView

#router = DefaultRouter()
router = DefaultRouter(trailing_slash=False)
router.register(r'requisitions', RequisitionViewSet, basename='requisitions')
router.register(r'inventories', InventoriesViewSet, basename='inventories')
router.register(r"debit-vouchers", DebitVoucherViewSet, basename="debit-voucher")
router.register(r"credit-vouchers", CreditVoucherViewSet, basename="credit-voucher")
router.register(r'ledger', LedgerEntryViewSet, basename='ledger-entry')
router.register(r'transaction', TransactionLedgerViewSet, basename='transaction-ledger')
router.register(r"notifications", NotificationViewSet, basename="notification")
router.register(r'project-boq', ProjectBOQViewSet, basename='project-boq')
router.register(r'customers', CustomerViewSet, basename='customers')
router.register(r'rooms', RoomViewSet, basename='room')
router.register(r'rooms-active', ActiveRoomViewSet, basename='active-room')
router.register(r'rooms-deactive', DeactiveRoomViewSet, basename='deactive-room')
router.register(r'bills', BillViewSet, basename='bill')
router.register(r'rents', RentViewSet, basename='rent')
router.register(r'receive-vouchers', ReceiveVoucherViewSet, basename='receive-voucher')
router.register(r'payment-vouchers', PaymentVoucherViewSet, basename='payment-voucher')
router.register(r'ledger-tenant', LedgerEntryCustomViewSet, basename='ledger-tenant')
router.register(r'ledger-trail', LedgerEntryCustomtrailViewSet, basename='ledger-trail')
router.register(r'heads', HeadOfAccountViewSet, basename='head')
router.register(r'banks', CashTypeViewSet, basename='bank')
router.register(r'projects', ProjectFirstLevelNameViewSet, basename='projects')
router.register(r'vendors', SuppliersViewSet, basename='vendors')
router.register(r'contractors', SiteSupervisorViewSet, basename='contractors')



urlpatterns = [
    path('', include(router.urls)),    
    path('api/v1/auth/login/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('api/v1/auth/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
]




