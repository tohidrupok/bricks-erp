from django.urls import path
from . import views

urlpatterns = [
    path('', views.bill_generator_home, name="bill_generator_home"),
    path('dashboard/', views.tenant_dashboard, name='tenant_dashboard'),
    path('projects/', views.project_page, name='project_page'),


    # Varatiya URLs
    path('varatiya/', views.varatiya_form_and_list, name='varatiya_list'),
    path('varatiya/<int:pk>/edit/', views.varatiya_update, name='varatiya_update'),
    path('varatiya/<int:pk>/delete/', views.varatiya_delete, name='varatiya_delete'),
    path("varatiya/<int:pk>/", views.varatiya_detail, name="varatiya_detail"),

    # Room URLs
    path('room/', views.room_list, name='room_list'),
    path('room/create/', views.room_create, name='room_create'),
    path('room/<int:pk>/edit/', views.room_update, name='room_update'),
    path('room/<int:pk>/delete/', views.room_delete, name='room_delete'),
    path("rooms/<int:room_id>/", views.room_details, name="room_details"),

    path('rent/', views.rent_list, name='rent_list'), 
    path('rent/create/', views.rent_create, name='rent_create'),
    path('ajax/load-rooms/', views.load_rooms, name='ajax_load_rooms'),
    path('rent/list/', views.rent_form_and_list, name='rent_form_and_list'),

    path('rent/search/', views.rent_search, name='rent_search'),
    path('ajax/load-deactive-rooms/', views.deactiveload_rooms, name='ajax_load_deactive_rooms'),


    path('rent/deactivate/<int:rent_id>/', views.deactivate_rent, name='deactivate_rent'),

    path("bill-generate/", views.bill_generate, name="bill_generate"),
    path("bill-generate/<int:project_id>/", views.get_project_rooms, name="get_project_rooms"),
    path("generate-bill/", views.save_generated_bill, name="save_generated_bill"),
    path("bulk-print/", views.bulk_print_bills, name="bulk_print_bills"),


    path("gas-bill/", views.gas_bill_generate, name="gas_bill_generate"),
    path("gas-bill/project/<int:project_id>/rooms/", views.get_project_gas_rooms, name="get_project_gas_rooms"),
    path("gas-bill/project/create/", views.create_gas_bills, name="create_gas_bills"),
    path('gas-bill/print/', views.bulk_print_gas_bills, name='bulk_print_gas_bills'),


    path("water-bill/", views.water_bill_generate, name="water_bill_generate"),
    path("water-bill/project/<int:project_id>/rooms/", views.get_project_water_rooms, name="get_project_water_rooms"),
    path("water-bill/project/create/", views.create_water_bills, name="create_water_bills"),
    path("water-bill/print/", views.bulk_print_water_bills, name="bulk_print_water_bills"),

    path("parking-bill/", views.parking_bill_generate, name="parking_bill_generate"),
    path("parking-bill/project/<int:project_id>/rooms/", views.get_project_parking_rooms, name="get_project_parking_rooms"),
    path("parking-bill/project/create/", views.create_parking_bills, name="create_parking_bills"),
    path("parking-bill/print/", views.bulk_print_parking_bills, name="bulk_print_parking_bills"),


    # Electricity Bill URLs
    # path("electricity-bill/", views.electricity_bill_generate, name="electricity_bill_generate"),
    # path("electricity-bill/project/<int:project_id>/rooms/", views.get_project_electricity_rooms, name="get_project_electricity_rooms"),
    # path("electricity-bill/project/create/", views.create_electricity_bills, name="create_electricity_bills"),
 
    path("service-bill/", views.service_bill_generate, name="service_bill_generate"),
    path("service-bill/project/<int:project_id>/rooms/", views.get_project_service_rooms, name="get_project_service_rooms"),
    path("service-bill/project/create/", views.create_service_bills, name="create_service_bills"),
    path('service-bill/print/', views.bulk_print_service_bills, name='bulk_print_service_bills'),
 
    path("garbage-bill/", views.garbage_bill_generate, name="garbage_bill_generate"),
    path("garbage-bill/project/<int:project_id>/rooms/", views.get_project_garbage_rooms, name="get_project_garbage_rooms"),
    path("garbage-bill/project/create/", views.create_garbage_bills, name="create_garbage_bills"),
    path("garbage-bill/print/", views.bulk_print_garbage_bills, name="bulk_print_garbage_bills"),

    path("electricity/generate/", views.electricity_bill_generate, name="electricity_bill_generate"),
    path("electricity/get-rents/<int:project_id>/", views.get_project_electricity_rents, name="get_project_electricity_rents"),
    path("electricity/save/", views.save_electricity_bill, name="save_electricity_bill"),
    path("electricity-bill/print/", views.bulk_print_electricity_bills, name="bulk_print_electricity_bills"),

    path('main-bill/report/', views.main_bill_list, name='main_bill_list'),
    path('mainbills/', views.mainbill_list, name='mainbill_list'),
    path('mainbill/<int:pk>/apply-discount/', views.apply_discount_to_mainbill, name='apply_discount_to_mainbill'),



    path('tenant-ledger/', views.tenant_ledger_input_page, name='tenant_ledger_input_page'),
    path('tenant-ledger/result/', views.tenant_ledger_result_page, name='tenant_ledger_result_page'),
    path('tenant-ledger/print/', views.tenant_ledger_print, name='tenant_ledger_print'),
    path('ajax/project/<int:project_id>/varatiyas/', views.get_project_varatiyas, name='get_project_varatiyas'),
    path('ajax/varatiya/<int:varatiya_id>/ledger/', views.get_varatiya_ledger, name='get_varatiya_ledger'),
    path("advance/add/", views.add_tenant_advance, name="add_tenant_advance"),
    path('advance/list/', views.tenant_advance_list, name='tenant_advance_list'),
    path('advance/delete/<int:advance_id>/', views.delete_tenant_advance, name='delete_tenant_advance'),
    path("get-cheques/<int:cash_type_id>/", views.get_cheques_by_cash_type, name="get_cheques_by_cash_type"),


    path('ajax/get_varatiyas/<int:project_id>/', views.get_project_varatiyas, name='get_project_varatiyas'),
    path('ajax/bill_summary/', views.project_varatiya_bills, name='project_varatiya_bills'),
    path('bill_summary/', views.bill_summary_page, name='bill_summary_page'),
    path('ajax/create_receive_voucher/', views.create_receive_voucher, name='create_receive_voucher'),
    path('bill_view/', views.bill_view_page, name='bill_view'),

    # Receive Voucher URLs
    path('receive-vouchers/', views.receive_voucher_list, name='receive_voucher_list'),
    path('receive-voucher/<int:pk>/edit/', views.receive_voucher_edit, name='receive_voucher_edit'),
    path('receive-voucher/<int:pk>/delete/', views.receive_voucher_delete, name='receive_voucher_delete'),
    path('receivevoucher/<int:pk>/pdf/', views.receive_voucher_pdf, name='receivevoucher_pdf'),
    path('receive-voucher/approve/<int:pk>/', views.approve_receive_voucher, name='approve_receive_voucher'),

    # Payment Voucher URLs
    path('advance/payment/', views.payment_tenant_advance, name='payment_tenant_advance'),
    path('payment-vouchers/', views.payment_voucher_list, name='payment_voucher_list'),
    path('paymentvoucher/<int:pk>/pdf/', views.payment_voucher_pdf, name='paymentvoucher_pdf'),
    path('payment-voucher/approve/<int:pk>/', views.approve_payment_voucher, name='approve_payment_voucher'),
    
    path('supplier-payment/', views.supplier_payment_page, name="supplier_payment_page"),
    path('supplier-payment/create/', views.create_supplier_payment, name="create_supplier_payment"),
    path("supplier/add/", views.add_supplier, name="add_supplier"),
    
    path('books/', views.cheque_book_list, name='cheque_book_list'),
    path('books/<int:book_id>/cheques/', views.cheque_list, name='cheque_list'),

    path('edit-book/<int:pk>/', views.edit_book, name='edit_book'),
    path('delete-book/<int:pk>/', views.delete_book, name='delete_book'),

    path('edit-cheque/<int:pk>/', views.edit_cheque, name='edit_cheque'),
    path('delete-cheque/<int:pk>/', views.delete_cheque, name='delete_cheque'),
    
    path("iclock/cdata", views.iclock_cdata), 
    path('upload-csv/', views.upload_csv, name='upload_csv'),

    path('account/list/', views.tenantcash_list, name='account_list'),
    path('account/create/', views.tenantcash_create, name='account_create'),
    path('account/<int:pk>/', views.tenantcash_detail, name='account_detail'),
    path('account/<int:pk>/edit/', views.tenantcash_edit, name='account_edit'),
    path('account/<int:pk>/delete/', views.tenantcash_delete, name='account_delete'),
    
    
    
    path('varatiya-sms/', views.varatiya_bulk_sms, name='varatiya_bulk_sms'),
    path('sms-history/', views.varatiya_bulk_sms_list, name='varatiya_bulk_sms_list'),
    path('sms-history/<int:pk>/', views.varatiya_bulk_sms_list, name='sms_detail'),

]
