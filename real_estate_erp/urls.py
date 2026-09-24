from django.contrib import admin
from django.urls import path, include
from erp.views import home, login, register, dashboard, logout
from django.conf import settings
from django.conf.urls.static import static


# Import views with aliases
from properties import views as views
from documents import views as documents_views
from projects import views as  projects_views
from crm import views as  crm_views
from products import views as  products_view
from accounting import views as  accounting_views
from hrm import views as hrm_view
from purchase import views as purchase_view
from inventories import views as inventories_view
from sales import views as sales_view
from restahrm import views as restahrm_view
from restaccounting import views as restaccounting_view
from tasks import views as tasks_view

from restaurant import views as restaurant_view
from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
)
from erp_api.auth_views import CustomTokenObtainPairView
from .view import *

urlpatterns = [
    path('api/v1/', include('erp_api.urls')),
   
    path('api/v1/auth/login/', CustomTokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('api/v1/auth/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    
    
    # Admin task Views start -- 
    path('assign-task/', tasks_view.task_assign_btp_employee, name='task_assign_btp_employee'),
    path('employee-details/<int:employee_id>/', tasks_view.admin_employee_task_details, name='admin_employee_task_details'),
    
    # Async JSON Fetch Engine 
    path('ajax/load-employees/', tasks_view.load_employees, name='ajax_load_employees'),

    # Isolated Portal Access System Nodes
    path('my-tasks/', tasks_view.employee_task_dashboard, name='employee_task_dashboard'),
    path('my-tasks/<int:task_id>/complete/', tasks_view.complete_task_submit, name='complete_task_submit'),
    
    # Admin task Views End -- 
    
    
    path('', home, name='home'), 
    path('login/', login, name='login'), 
    path('register/', register, name='register'),  
    path('dashboard/', requisition_dashboard, name='dashboard'), 
    path('logout/', logout, name='logout'),
    path('admin/', admin.site.urls),
    path('tenant/', include('tenant.urls')),
    path('tracker/', include('tracker.urls')),
    path('pos/', include('pos.urls')),
    path('office_inventory/', include('office_inventory.urls')),
    path('whatsapp/', include('whatsapp.urls')),
    path("", include("menu_app.urls")),
    # path("dashboard/iclock/cdata", hrm_view.iclock_cdata, name='edit_user_permissions'), 
    path('dashboard/', requisition_dashboard, name='requisition_dashboard'),
    # PropertyOwner URLs ----
    path('dashboard/property_owner/', views.property_owner_list, name='property_owner_list'),
    path('dashboard/property_owner/add/', views.add_property_owner, name='add_property_owner'),
    path('dashboard/property_owner/<int:id>/detail/', views.property_owner_detail, name='property_owner_detail'),
    path('dashboard/property_owner/<int:id>/', views.edit_property_owner, name='edit_property_owner'),
    path('dashboard/property_owner/delete/<int:id>/', views.delete_property_owner, name='delete_property_owner'),
    
    path('dashboard/property_cradit/', views.land_creditvoucher_list, name='land_creditvoucher_list'),
    path('dashboard/property_cradit/add', views.add_land_creditvoucher, name='add_land_creditvoucher'),

    # Project URLs ---
    path('dashboard/project/', views.project_list, name='project_list'),
    path('dashboard/project/add/', views.add_project, name='add_project'),
    path('dashboard/project/<int:project_id>/detail/', views.project_detail, name='project_detail'),
    path('dashboard/project/<int:id>/', views.edit_project, name='edit_project'),
    path('dashboard/project/delete/<int:id>/', views.delete_project, name='delete_project'),

    # Property URLs ---   
    path('dashboard/property/', views.property_list, name='property_list'),
    path('dashboard/property/add/', views.add_property, name='add_property'),
    path('dashboard/property/<int:id>/detail/', views.property_detail, name='property_detail'),
    path('dashboard/property/<int:id>/edit/', views.edit_property, name='edit_property'),
    path('dashboard/property/<int:id>/delete/', views.delete_property, name='delete_property'),

    # JointVenture URLs    
    path('dashboard/joint_venture/', views.joint_venture_list, name='joint_venture_list'),  
    path('dashboard/joint_venture/add/', views.add_joint_venture, name='add_joint_venture'),
    path('dashboard/joint_venture/<int:id>/detail/', views.joint_venture_detail, name='joint_venture_detail'),
    path('dashboard/joint_venture/<int:id>/', views.edit_joint_venture, name='edit_joint_venture'),  
    path('dashboard/joint_venture/delete/<int:id>/', views.delete_joint_venture, name='delete_joint_venture'), 
    
    path('dashboard/joint_venture/installment', views.joint_venture_installment_management, name='joint_venture_installment_management'),

    # JVPartner URLs
    path('dashboard/jv_partner/', views.jv_partner_list, name='jv_partner_list'),
    path('dashboard/jv_partner/add/', views.add_jv_partner, name='add_jv_partner'),
    path('dashboard/jv_partner/<int:id>/detail/', views.jv_partner_detail, name='jv_partner_detail'),
    path('dashboard/jv_partner/<int:id>/', views.edit_jv_partner, name='edit_jv_partner'), 
    path('dashboard/jv_partner/delete/<int:id>/', views.delete_jv_partner, name='delete_jv_partner'),

    # Tenant URLs
    path('dashboard/tenant/', views.tenant_list, name='tenant_list'),
    path('dashboard/tenant/add/', views.add_tenant, name='add_tenant'),
    path('dashboard/tenant/<int:id>/detail/', views.tenant_detail, name='tenant_detail'),
    path('dashboard/tenant/<int:id>/', views.edit_tenant, name='edit_tenant'),
    path('dashboard/tenant/delete/<int:id>/', views.delete_tenant, name='delete_tenant'),
    path('dashboard/tenant/<int:tenant_id>/pay_history/', views.tenant_pay_history, name='tenant_pay_his'),

    # LeaseAgreement URLs
    path('dashboard/lease_agreement/', views.lease_agreement_list, name='lease_agreement_list'),
    path('dashboard/lease_agreement/add/', views.add_lease_agreement, name='add_lease_agreement'),
    path('dashboard/lease_agreement/<int:id>/detail/', views.lease_agreement_detail, name='lease_agreement_detail'),
    path('dashboard/lease_agreement/<int:id>/', views.edit_lease_agreement, name='edit_lease_agreement'),
    path('dashboard/lease_agreement/delete/<int:id>/', views.delete_lease_agreement, name='delete_lease_agreement'),
    
    # LeasePayment URLs
    path('dashboard/lease_payment/', views.lease_payment_list, name='lease_payment_list'),
    path('dashboard/lease_payment/add/', views.add_lease_payment, name='add_lease_payment'),
    path('dashboard/lease_payment/<int:id>/detail/', views.lease_payment_detail, name='lease_payment_detail'),
    path('dashboard/lease_payment/<int:id>/', views.edit_lease_payment, name='edit_lease_payment'),
    path('dashboard/lease_payment/delete/<int:id>/', views.delete_lease_payment, name='delete_lease_payment'),

    # Buyer URLs
    path('dashboard/buyer/', views.buyer_list, name='buyer_list'),
    path('dashboard/buyer/add/', views.add_buyer, name='add_buyer'),
    path('dashboard/buyer/<int:id>/detail/', views.buyer_detail, name='buyer_detail'),
    path('dashboard/buyer/<int:id>/', views.edit_buyer, name='edit_buyer'),
    path('dashboard/buyer/delete/<int:id>/', views.delete_buyer, name='delete_buyer'),
    path('dashboard/buyer/<int:buyer_id>/pay_history/', views.buyer_pay_history, name='buyer_pay_his'),

    # SaleRecord URLs
    path('dashboard/sale_record/', views.sale_record_list, name='sale_record_list'),
    path('dashboard/sale_record/add/', views.add_sale_record, name='add_sale_record'),
    path('dashboard/sale_record/<int:id>/detail/', views.sale_record_detail, name='sale_record_detail'),
    path('dashboard/sale_record/<int:id>/', views.edit_sale_record, name='edit_sale_record'),
    path('dashboard/sale_record/delete/<int:id>/', views.delete_sale_record, name='delete_sale_record'),


    ## land purchase--
    path('documents/new/file/list', views.new_document_list, name='new_document_list'),
    path('document/new/file/list', views.new_create_document, name='new_create_document'),
    path('document/new/check-doc-no/', views.check_doc_no, name='check_doc_no'),
    path('document/new/update-date/', views.update_doc_date, name='update_doc_date'),
    path('document/new/file/list<int:pk>/edit/', views.new_edit_document, name='new_edit_document'),
    path('document/new/file/list<int:pk>/delete/', views.new_delete_document, name='new_delete_document'),
    #path('document/new/file/detail/<int:id>/', views.new_land_document_row_detail, name='new_land_document_row_detail'),
    
    
    path('dashboard/file-records/view', views.file_record_list, name='file_record_list'),
    path('dashboard/file-records/upload-csv/upload/', views.upload_csv_upload, name='upload_csv_upload'),
    path('dashboard/file-records/upload-csv/', views.upload_csv, name='upload_record_csv'),
    path('records/file-records/new/', views.file_record_create, name='file_record_create'),
    path('records/view/<int:pk>/', views.file_record_detail, name='file_record_detail'),
    path('records/edit/<int:pk>/', views.file_record_update, name='file_record_update'),
    path('records/delete/<int:pk>/', views.file_record_delete, name='file_record_delete'),
    
    path('records/get-file-no/', views.get_next_file_no, name='get_next_file_no'),
    path('dashboard/file-records/',  views.file_record_dashboard, name='file_record_dashboard'),
    
    path('dashboard/land-purchase/view', views.land_dashboard, name='land_dashboard'),
    path('dashboard/land-purchase/', views.land_list, name='land_list'),
    path('dashboard/land-purchase/add/', views.land_add, name='land_add'),
    path('dashboard/land-purchase/edit/<int:pk>/', views.land_edit, name='land_edit'),
    path('dashboard/land-purchase/delete/<int:pk>/', views.land_delete, name='land_delete'),
    path('dashboard/land-purchase/detail/<int:pk>/', views.land_detail, name='land_detail'),
    
    path('dashboard/land/<int:pk>/approve/', views.approve_land_voucher, name='approve_land_voucher'),
    
    path('dashboard/lilahetalah-list/', views.lilahetalah_list, name='lilahetalah_list'),
    path('dashboard/lilahetalah-hostory/detail/<int:pk>/', views.lilahetalah_details, name='lilahetalah_details'),
    path('dashboard/media-pay-list/', views.media_pay_list, name='media_pay_list'),
    path('dashboard/media-pay-hostory/detail/<int:pk>/', views.media_pay_details, name='media_pay_details'),
    path('dashboard/land-ledger/list/', views.land_ledger_list, name='land_ledger_list'),
    path('dashboard/land-ledger/filter-new/', views.filter_land_ledger_new, name='filter_land_ledger_new'),
    
    path('dashboard/land/payments/', views.land_payment_list, name='land_payment_list'),
    path('dashboard/land-app-pay-pdf/<int:owner_id>/', views.land_payment_pdf, name='land_payment_pdf'),
    path('dashboard/owner-payment/add/<int:id>/', views.land_owner_payment, name='land_owner_payment'),
    path('update-payment/<int:payment_id>/', views.update_payment_amount, name='update_payment_amount'),
    
    
    path('dashboard/land-debitvouchers/', views.land_debitvoucher_list, name='land_debitvoucher_list'),
    path('dashboard/land-debitvouchers/add/', views.add_land_debitvoucher, name='add_land_debitvoucher'),
    path('dashboard/land-debitvouchers/edit/<int:pk>/', views.edit_land_debitvoucher, name='edit_land_debitvoucher'),
    path('dashboard/land-debitvouchers/delete/<int:pk>/', views.land_delete_debitvoucher, name='land_delete_debitvoucher'),
    #path('dashboard/land-debitvouchers/<int:pk>/', views.details_debitvoucher, name='details_debitvoucher'),
    path('dashboard/land-debit-voucher/<int:pk>/pdf/', views.land_debit_voucher_pdf, name='land_debit_voucher_pdf'),
    path('dashboard/land-approve-debit-voucher/<int:pk>/', views.approve_land_pay_voucher, name='approve_land_pay_voucher'),
    
    
    
    ###  Land Expense Head ###
    path('dashboard/land-head-of-expense/', views.land_expense_head_list, name='land_expense_head_list'),
    path('dashboard/land-head-of-expense/add/', views.add_land_head_of_expense, name='add_land_head_of_expense'),
    path('dashboard/land-head-of-expense/edit/<int:pk>/', views.edit_land_head_of_expense, name='edit_land_head_of_expense'),
    path('dashboard/land-head-of-expense/delete/<int:pk>/', views.delete_land_head_of_expense, name='delete_land_head_of_expense'),
    

    # -- documents app --
    path('dashboard/document/', documents_views.document_list, name='document_list'),
    path('dashboard/upload/', documents_views.upload_document, name='upload_document'),
    path('dashboard/documents/<int:document_id>/versions/', documents_views.document_versions, name='document_versions'),
    #path('dashboard/documents/<int:document_id>/versions/', documents_views.document_versions, name='document_versions'), 
    path('dashboard/documents/<int:document_id>/upload_version/', documents_views.upload_document_version, name='upload_document_version'),
    path('dashboard/property/<int:property_id>/', documents_views.document_list, name='property_documents'),

    path('dashboard/display/', documents_views.display, name='display'),  
    path('dashboard/display/<int:folder_id>/', documents_views.display, name='display_folder'),
    path('dashboard/page/<int:folder_id>/', documents_views.page, name='page'),  
    path('dashboard/create_folder/', documents_views.create_folder, name='create_folder'),
    path('dashboard/file/edit/<int:file_id>/', documents_views.edit_file_name, name='edit_file_name'),
  

    path('dashboard/rename-folder/<int:folder_id>/', documents_views.rename_folder, name='rename_folder'),
    path('dashboard/delete-folder/<int:folder_id>/', documents_views.delete_folder, name='delete_folder'),
    path('dashboard/delete-file/<int:file_id>/', documents_views.delete_file, name='delete_file'),
    
    
    path('dashboard/display/tracker', documents_views.tracker_display, name='tracker_display'),  
    path('dashboard/display/tracker/<int:folder_id>/', documents_views.tracker_display, name='tracker_display_folder'),
    path('dashboard/page/tracker/<int:folder_id>/', documents_views.tracker_page, name='tracker_page'),  
    path('dashboard/create_folder/tracker/', documents_views.tracker_create_folder, name='tracker_create_folder'),
    path('dashboard/file/edit/tracker<int:file_id>/', documents_views.tracker_edit_file_name, name='tracker_edit_file_name'),
  

    path('dashboard/rename-folder/tracker/<int:folder_id>/', documents_views.tracker_rename_folder, name='tracker_rename_folder'),
    path('dashboard/delete-folder/tracker/<int:folder_id>/', documents_views.tracker_delete_folder, name='tracker_delete_folder'),
    path('dashboard/delete-file/tracker/<int:file_id>/', documents_views.tracker_delete_file, name='tracker_delete_file'),
    
    
    path('google-drive/files/', documents_views.google_tracker_file_system, name='google_tracker_file_system'),
    path('google-drive/test-save/', documents_views.google_drive_test_save, name='google_drive_test_save'),
    path('google-drive/test-api/', documents_views.google_drive_test_api, name='google_drive_test_api'),
    path('google-drive/files/<int:folder_id>/', documents_views.google_tracker_file_system, name='google_tracker_file_system_folder'),
    path('google-drive/files/sync/<int:folder_id>/', documents_views.google_tracker_sync_drive, name='google_tracker_sync_drive'),
    path('google-drive/files/delete/<int:file_id>/', documents_views.google_tracker_delete_file, name='google_tracker_delete_file'),
    path('google-drive/files/edit/<int:file_id>/', documents_views.google_tracker_edit_file_name, name='google_tracker_edit_file_name'),
    path('google-drive/api/drive/browse/', documents_views.google_tracker_drive_browse, name='google_tracker_drive_browse'),
    
    
    path('dashboard/employe-document/', documents_views.emp_document, name='emp_document'),
    path('dashboard/employe-document/<int:folder_id>/', documents_views.emp_document, name='emp_display_folder'),
    path('dashboard/employe-rename-folder/<int:folder_id>/', documents_views.emp_rename_folder, name='emp_rename_folder'),
    path('dashboard/employe-delete-folder/<int:folder_id>/', documents_views.emp_delete_folder, name='emp_delete_folder'),
    
    # Updated path to view subfolders and files inside a specific folder
    path('dashboard/employe-page/<int:folder_id>/', documents_views.emp_page, name='emp_page'),
    
    # File Operations
    path('dashboard/employe-file/edit/<int:file_id>/', documents_views.emp_edit_file_name, name='emp_edit_file_name'),
    path('dashboard/employe-delete-file/<int:file_id>/', documents_views.emp_delete_file, name='emp_delete_file'),
    
    # Admin Move Actions
    path('dashboard/move-folder/<int:folder_id>/', documents_views.emp_move_folder, name='emp_move_folder'),
    path('dashboard/move-file/<int:file_id>/', documents_views.emp_move_file, name='emp_move_file'),
    
    
    
    
    

    # Project Location URLs ---
    path('dashboard/locations/', projects_views.project_location_list, name='project_location_list'),
    path('dashboard/locations/add/', projects_views.project_location_add, name='project_location_add'),
    path('dashboard/locations/edit/<int:pk>/', projects_views.project_location_edit, name='project_location_edit'),
    path('dashboard/locations/delete/<int:pk>/', projects_views.project_location_delete, name='project_location_delete'),

    ## Project First Level --
    path('dashboard/boq/', projects_views.boq_list, name='boq_list'),
    path('dashboard/boq_details/list/', projects_views.boqdetails_list, name='boqdetails_list'),
    path('dashboard/boq-list/<int:project_id>/', projects_views.boq_list_details, name='boq_list_details'),
    # path('dashboard/boq-list/<str:project_name>/', projects_views.boq_list_details, name='boq_list_details'),
    path('dashboard/boq/add/', projects_views.boq_mate_create, name='boq_mate_create'), 
    #path('dashboard/boq/view/<int:pk>/', projects_views.boq_view, name='boq_view'),
    path('dashboard/boq/edit/<int:pk>/', projects_views.boq_edit, name='boq_edit'),  
    path('dashboard/boq/delete/<int:pk>/', projects_views.boq_delete, name='boq_delete'),
    path('dashboard/project_boq_details/', projects_views.project_boq_details, name='project_boq_details'),
    path('dashboard/boq/<int:project_id>/pdf/', projects_views.boq_pdf_view, name='boq_pdf'),
    path('dashboard/boq/eng/<int:project_id>/pdf/', projects_views.eng_boq_pdf_view, name='eng_boq_pdf'),
    path('dashboard/boq/category-pdf/', projects_views.boq_category_pdf, name='boq_category_pdf'),
    
    path('dashboard/project-boq-details-check/', projects_views.project_boq_details_check, name='project_boq_details_check'),
    path('dashboard/project-boq-details-view/', projects_views.project_boq_details_view, name='project_boq_details_view'),

    path('dashboard/boq/revise/<int:pk>/<int:project_id>/', projects_views.revise_boq, name='boq_revise'),

    path('dashboard/revised-item-entry/', projects_views.revised_item_entry, name='revised_item_entry'),

    #BOQ- type create
    path('dashboard/boqtype/add/', projects_views.create_boq_type, name='create_boq_type'),
    path('dashboard/boqtype/edit/<int:pk>/', projects_views.boq_type_edit, name='boq_type_edit'),
    path('dashboard/boqtype/delete/<int:pk>/', projects_views.boq_type_delete, name='boq_type_delete'),
    path('dashboard/boqtype/list/', projects_views.boq_type_list, name='boq_type_list'),
    
    path('dashboard/material-entry/list', projects_views.materialentry_list, name='materialentry_list'),
    path('dashboard/material-entry/add', projects_views.material_entry_create, name='material_entry_create'),

    path('dashboard/create-type/', projects_views.add_boq_type_only, name='add_boq_type_only'),
    path('dashboard/create/', projects_views.create_boq_category, name='create_boq_category'),
    path('dashboard/list/', projects_views.boq_category_list, name='boq_category_list'),
    path('dashboard/boq-category/edit/<int:id>/', projects_views.edit_boq_category, name='boq_category_edit'),
    path('dashboard/boq-category/delete/<int:id>/', projects_views.delete_boq_category, name='boq_category_delete'),

    path('dashboard/first-level/', projects_views.first_level_list, name='first_level_list'),
    path('dashboard/first-level/details/<int:pk>/',projects_views.first_level_details, name='first_level_details'),


    path('dashboard/first-level/details/<int:pk>/project-intro/',projects_views.project_intro,name='project_intro'),
    path('dashboard/first-level/details/<int:pk>/agreement-land/',projects_views.agreement_land, name='agreement_land'),
    path('dashboard/first-level/details/<int:pk>/schedule/',projects_views.project_schedule,name='project_schedule'),
    path( 'dashboard/first-level/details/<int:pk>/test/',projects_views.project_test, name='project_test'),
    path('dashboard/first-level/details/<int:pk>/drawing/',projects_views.project_drawing,name='project_drawing'),
    path('dashboard/first-level/details/<int:pk>/certificate/', projects_views.project_certificate,name='project_certificate'),
    path('dashboard/first-level/details/<int:pk>/approval/',projects_views.project_approval, name='project_approval'),
    path('dashboard/first-level/details/<int:pk>/schedule/crud/', projects_views.project_schedule_crud, name='project_schedule_crud'),
    
    # path('dashboard/first-level/details/<int:pk>/comparison/', projects_views.project_comparison, name='project_comparison'),
    # path( 'dashboard/first-level/details/<int:pk>/vendor/',projects_views.project_vendor,name='project_vendor'),
    # path('dashboard/first-level/details/<int:pk>/fund-receive/', projects_views.fund_receive, name='fund_receive'),
    # path('dashboard/first-level/details/<int:pk>/budget-expense-boq/',projects_views.budget_expense_boq, name='budget_expense_boq'),



    path('dashboard/add/', projects_views.first_level_add, name='first_level_add'), 
    path('dashboard/edit/<int:pk>/', projects_views.first_level_edit, name='first_level_edit'), 
    path('dashboard/delete/<int:pk>/', projects_views.first_level_delete, name='first_level_delete'),

    path('dashboard/project_flevel_details/', projects_views.project_flevel_details, name='project_flevel_details'),
    path('dashboard/projet_details/<int:project_id>/pdf/', projects_views.pfld_pdf_view, name='pfld_pdf'),
    
    path('dashboard/employee', projects_views.employee_costing, name='employee_costing'),
    path('dashboard/save-employees/', projects_views.save_employees, name='save_employees'), 
    path('dashboard/safety-equipment/',  projects_views.safety_equipment_view, name='safety_equipment_view'),
    path('dashboard/save_safety_equipment/',  projects_views.save_safety_equipment, name='save_safety_equipment'),
    path('dashboard/expense-view/',  projects_views.expense_view, name='expense_view'),
    path('dashboard/save-expense/',  projects_views.save_expense, name='save-expense'),
    #path('dashboard/boq/', projects_views.boq_view, name='boq_create'),

    path('dashboard/labor-cost', projects_views.labor_cost_create, name='labor_cost_create'),
    
    path('dashboard/contructor/', projects_views.boq_contructor_list, name='boq_contructor_list'),
    path('dashboard/contructor/add/', projects_views.create_boq_contructor, name='create_boq_contructor'),
    path('dashboard/boq-contructor/edit/<int:id>/', projects_views.edit_boq_contructor, name='edit_boq_contructor'),
    path('dashboard/boq-contructor/delete/<int:id>/', projects_views.delete_boq_contructor, name='delete_boq_contructor'),
    path('dashboard/contractor/<int:id>/', projects_views.contractor_detail, name='contractor_detail'),

    path('dashboard/Supplier/', projects_views.boq_supplier_list, name='boq_supplier_list'),
    path('dashboard/Supplier/add/', projects_views.create_boq_supplier, name='create_boq_supplier'),
    path('dashboard/boq-Supplier/edit/<int:id>/', projects_views.edit_boq_supplier, name='edit_boq_supplier'),
    path('dashboard/boq-Supplier/delete/<int:id>/', projects_views.delete_boq_supplier, name='delete_boq_supplier'),
    path('dashboard/supplier/<int:pk>/details/', projects_views.supplier_detail, name='boq_supplier_detail'),
    path('dashboard/Supplier/view/all/', projects_views.boq_supplier_details_view, name='boq_supplier_details_view'),

    
    ## --Donation ---
    path('dashboard/Donation/', projects_views.donation_list, name='donation_list'),
    path('dashboard/Donation/add/', projects_views.create_donation, name='create_donation'),
    path('dashboard/Donation/edit/<int:id>/', projects_views.edit_donation, name='edit_donation'),
    path('dashboard/Donation/delete/<int:id>/', projects_views.delete_donation, name='delete_donation'),
    path('dashboard/Donation/<int:pk>/details/', projects_views.donation_detail, name='donation_detail'),
    
    
    
    ## Contractor Activity
    path('dashboard/contractor/list', projects_views.activity_list, name='activity_list'),
    path('dashboard/contractor/add/', projects_views.activity_add, name='activity_add'),
    path('dashboard/contractor/<int:pk>/details', projects_views.activity_detail, name='activity_detail'),
    path('dashboard/contractor/<int:pk>/edit/', projects_views.activity_edit, name='activity_edit'),
    path('dashboard/contractor/<int:pk>/delete/', projects_views.activity_delete, name='activity_delete'),
    path('dashboard/contractor/Summary/', projects_views.activity_summary, name='activity_summary'),
    path('dashboard/update-activity-status/<int:pk>/', projects_views.update_activity_status, name='update_activity_status'),


    
    ###   CRM Module ###
    path('dashboard/customers/bank/list', crm_views.customer_bank, name='customer_bank'),
    path('dashboard/customers/bank/add/', crm_views.customer_bank_add, name='customer_bank_add'),
    path('dashboard/customers/bank/edit/<int:pk>/', crm_views.customer_bank_edit, name='customer_bank_edit'),
    path('dashboard/customers/bank/details/<int:pk>/', crm_views.customer_bank_details, name='customer_bank_details'),
    path('dashboard/customers/bank/delete/<int:pk>/', crm_views.customer_bank_delete, name='customer_bank_delete'),
    
    path('dashboard/customers/sms-send/', crm_views.bulk_sms_send_view, name='bulk_sms_send'),
    path('dashboard/customers/sms-send-details/', crm_views.bulk_sms_recipient_list, name='bulk_sms_recipient_list'),
    
    
    path('dashboard/customers/', crm_views.customer_list, name='customer_list'),
    path('dashboard/customers/add/', crm_views.customer_add, name='customer_add'),
    path('dashboard/customers/edit/<int:pk>/', crm_views.customer_edit, name='customer_edit'),
    path('dashboard/customers/details/<int:pk>/', crm_views.customer_details, name='customer_details'),
    path('dashboard/customers/delete/<int:pk>/', crm_views.customer_delete, name='customer_delete'),

    path('dashboard/customer_leads/', crm_views.customer_lead_list, name='customer_lead_list'),
    path('dashboard/customer_leads/add/', crm_views.customer_lead_add, name='customer_lead_add'),
    
    path('dashboard/leads-followup/list/', crm_views.lead_followup_list, name='lead_followup_list'),
    path('dashboard/leads/<int:lead_id>/toggle-status/', crm_views.toggle_lead_status, name='toggle_lead_status'),
    path('dashboard/leads-followup/<int:lead_id>/view/', crm_views.customer_lead_followup, name='customer_lead_followup'),


    path('lead-modal/<int:lead_id>/', crm_views.load_lead_modal, name='load_lead_modal'),
    path('crm/dashboard/', crm_views.crm_dashboard, name='crm_dashboard'),
    
    path('dashboard/customer_leads/edit/<int:pk>/', crm_views.customer_lead_edit, name='customer_lead_edit'),
    path('dashboard/customer_leads/delete/<int:pk>/', crm_views.customer_lead_delete, name='customer_lead_delete'),
    path('dashboard/customer-leads/<int:pk>/', crm_views.customer_lead_detail, name='customer_lead_detail'),
    
    path('dashboard/campaigns/', crm_views.campaign_list, name='campaign_list'),
    path('dashboard/campaigns/add/', crm_views.campaign_add, name='campaign_add'),
    path('dashboard/campaigns/view/<int:pk>/', crm_views.campaign_detail, name='campaign_detail'),
    path('dashboard/campaigns/edit/<int:pk>/', crm_views.campaign_edit, name='campaign_edit'),
    path('dashboard/campaigns/delete/<int:pk>/', crm_views.campaign_delete, name='campaign_delete'),
    path('leads/<int:lead_id>/stop-activity/', crm_views.stop_lead_activity, name='stop_lead_activity'),
    
    path('dashboard/leads/', crm_views.lead_list, name='lead_list'),
    
    # Lead Add & Edit
    path('dashboard/leads/create/', crm_views.lead_create_or_update, name='lead_create'),
    path('dashboard/leads/<int:lead_id>/edit/', crm_views.lead_create_or_update, name='lead_edit'),
    
    
    path('leads/<int:lead_id>/edit-modal/', crm_views.lead_edit_modal, name='lead_edit_modal'),
    path('leads/<int:lead_id>/update/', crm_views.lead_create_or_update, name='lead_update'),
    
    # Lead Activity / Detail Pop-up
    path('dashboard/leads/<int:lead_id>/activity/', crm_views.lead_activity_detail, name='lead_activity_detail'),
    
    # Action Endpoints
    path('dashboard/leads/<int:lead_id>/delete/', crm_views.lead_delete, name='lead_delete'),
    path('dashboard/leads/convert-customer/', crm_views.convert_to_customer, name='convert_to_customer'),
    path('dashboard/leads/<int:lead_id>/add-activity/', crm_views.add_lead_activity, name='add_lead_activity'),
    
    

    ###   Products Module ###
    path('dashboard/products/', products_view.product_list, name='product_list'),
    path('dashboard/products/add/', products_view.add_product, name='add_product'),

    ###   Accounting Module ###
    path('dashboard/cash-types/', accounting_views.cash_type_list, name='cash_type_list'),
    path('dashboard/cash-types/add/', accounting_views.add_cash_type, name='add_cash_type'),
    path('dashboard/cash-types/edit/<int:pk>/', accounting_views.edit_cash_type, name='edit_cash_type'),
    path('dashboard/cash-types/delete/<int:pk>/', accounting_views.delete_cash_type, name='delete_cash_type'),
    
    ## cheque manage ---
    path('dashboard/main-books/list', accounting_views.main_cheque_book_list, name='main_cheque_book_list'),
    path('dashboard/main-books/print/<int:book_id>/', accounting_views.cheque_book_print, name='cheque_book_print'),
    path('dashboard/main-books/list/<int:book_id>/cheques/', accounting_views.main_cheque_list, name='main_cheque_list'),
    path('dashboard/get-cheques/<int:cash_type_id>/', accounting_views.get_cheques_by_cash_type, name='get_cheques_by_cash_type'),
    
    
    
    path('dashboard/main-edit-book/<int:pk>/', accounting_views.main_edit_book, name='main_edit_book'),
    path('dashboard/main-delete-book/<int:pk>/', accounting_views.main_delete_book, name='main_delete_book'),

    path('dashboard/main-edit-cheque/<int:pk>/', accounting_views.main_edit_cheque, name='main_edit_cheque'),
    path('dashboard/main-delete-cheque/<int:pk>/', accounting_views.main_delete_cheque, name='main_delete_cheque'),
    
    
    ## --head of accounting---
    path('dashboard/head-of-accounts/', accounting_views.head_of_account_list, name='head_of_account_list'),
    path('dashboard/head-of-accounts/add/', accounting_views.add_head_of_account, name='add_head_of_account'),
    path('dashboard/head-of-accounts/edit/<int:pk>/', accounting_views.edit_head_of_account, name='edit_head_of_account'),
    path('dashboard/head-of-accounts/delete/<int:pk>/', accounting_views.delete_head_of_account, name='delete_head_of_account'),
    
    ###   credit voucher ###
    path('dashboard/creditvouchers/', accounting_views.creditvoucher_list, name='creditvoucher_list'),
    path('dashboard/creditvouchers/add/', accounting_views.add_creditvoucher, name='add_creditvoucher'),
    path('dashboard/creditvouchers/edit/<int:pk>/', accounting_views.edit_creditvoucher, name='edit_creditvoucher'),
    path('dashboard/creditvouchers/delete/<int:pk>/', accounting_views.delete_creditvoucher, name='delete_creditvoucher'),
    path('dashboard/creditvouchers/<int:pk>/', accounting_views.details_creditvoucher, name='details_creditvoucher'),
    path('dashboard/credit-voucher/<int:pk>/pdf/', accounting_views.credit_voucher_pdf, name='credit_voucher_pdf'),
    path('dashboard/approve/<int:pk>/', accounting_views.approve_cr_voucher, name='approve_cr_voucher'),


    ###   debit voucher ###
    path('dashboard/debitvouchers/', accounting_views.debitvoucher_list, name='debitvoucher_list'),
    path('dashboard/debitvouchers/add/', accounting_views.add_debitvoucher, name='add_debitvoucher'),
    path('dashboard/debitvouchers/edit/<int:pk>/', accounting_views.edit_debitvoucher, name='edit_debitvoucher'),
    path('dashboard/debitvouchers/delete/<int:pk>/', accounting_views.delete_debitvoucher, name='delete_debitvoucher'),
    path('dashboard/debitvouchers/<int:pk>/', accounting_views.details_debitvoucher, name='details_debitvoucher'),
    path('dashboard/debit-voucher/<int:pk>/pdf/', accounting_views.debit_voucher_pdf, name='debit_voucher_pdf'),
    path('dashboard/approve-debit-voucher/<int:pk>/', accounting_views.approve_dr_voucher, name='approve_dr_voucher'),

    path('dashboard/vendor-cashtype-update/', accounting_views.vendor_cashtype_update, name='vendor_cashtype_update'),
    path('dashboard/vendor-cashtype-update-submit/', accounting_views.vendor_cashtype_update_submit, name='vendor_cashtype_update_submit'),


    ###   journal voucher ###
    path('dashboard/journal-vouchers/', accounting_views.journal_voucher_list, name='journal_voucher_list'),
    path('dashboard/journal-vouchers/add/', accounting_views.journal_voucher_add, name='journal_voucher_add'),
    path('dashboard/journal-vouchers/<int:pk>/edit/', accounting_views.journal_voucher_edit, name='journal_voucher_edit'),
    path('dashboard/journal-vouchers/<int:pk>/delete/', accounting_views.journal_voucher_delete, name='journal_voucher_delete'),
    path('dashboard/journal-voucher/<int:pk>/pdf/', accounting_views.journal_voucher_pdf, name='journal_voucher_pdf'),
    
    ###   Contra voucher ###
    path('dashboard/Contra-Voucher', accounting_views.contra_voucher_list, name='contra_voucher_list'),
    path('dashboard/Contra-Voucher/add/', accounting_views.contra_voucher_add, name='contra_voucher_add'),
    path('dashboard/Contra-Voucher/edit/<int:pk>/', accounting_views.contra_voucher_edit, name='contra_voucher_edit'),
    path('dashboard/Contra-Voucher/delete/<int:pk>/', accounting_views.contra_voucher_delete, name='contra_voucher_delete'),
    path('dashboard/Contra-voucher/<int:pk>/pdf/', accounting_views.contra_voucher_pdf, name='contra_voucher_pdf'),

    ###  Ledger Manage ###
    path('dashboard/ledger-manage/list', accounting_views.ledger_manage_list, name='ledger_manage_list'),
    path('dashboard/ledger-manage/add', accounting_views.ledger_manage_add, name='ledger_manage_add'),    
    path('dashboard/ledger-manage/edit/<int:pk>/', accounting_views.ledger_manage_edit, name='ledger_manage_edit'),    
    path('dashboard/ledger-manage/delete/<int:pk>/', accounting_views.ledger_entry_delete, name='ledger_manage_delete'),
    

    ###  transaction history ###
    path('dashboard/transaction-history/', accounting_views.transaction_history_list, name='transaction_history_list'),
    path('dashboard/cahs-type-blance/', accounting_views.cashType_balance_list, name='cashType_balance_list'),

    path('dashboard/chartered-accountant/<int:head_id>/', accounting_views.head_wise_transaction_view, name='head_wise_transaction'),

    ###  transfer history ###
    path('dashboard/transfers/', accounting_views.transfer_list, name='transfer_list'),
    path('dashboard/transfers/add/', accounting_views.transfer_add, name='transfer_add'), 
    path('dashboard/transfers/<int:pk>/details', accounting_views.transfer_detail, name='transfer_detail'),
    
    path('project-balance-transfers/', accounting_views.project_transfer_list, name='project_transfer_list'),
    path('project-balance-transfers/add/', accounting_views.project_transfer_add, name='project_transfer_add'),
    path('project-balance-transfers/<int:pk>/edit/', accounting_views.project_transfer_edit, name='project_transfer_edit'),
    path('project-balance-transfers/<int:pk>/delete/', accounting_views.project_transfer_delete, name='project_transfer_delete'),
    path('project-balance-transfers/transfers/<int:pk>/', accounting_views.project_transfer_detail, name='project_transfer_detail'),
    
    ###   Loan voucher ###
    path('dashboard/payable/list', accounting_views.loanvoucher_list, name='loanvoucher_list'),
    path('dashboard/payable-amount/list', accounting_views.loanvoucher_pay_list, name='loanvoucher_pay_list'),
    path('dashboard/received-amount/list', accounting_views.loanvoucher_recv_list, name='loanvoucher_recv_list'),
    path('dashboard/payable/add/', accounting_views.add_loanvoucher, name='add_loanvoucher'),
    path('dashboard/received/add/', accounting_views.add_rechvoucher, name='add_rechvoucher'),
    path('dashboard/payable/edit/<int:pk>/', accounting_views.edit_loanvoucher, name='edit_loanvoucher'),
    path('dashboard/payable/delete/<int:pk>/', accounting_views.delete_loanvoucher, name='delete_loanvoucher'),
    path('dashboard/payable/<int:pk>/', accounting_views.details_loanvoucher, name='details_loanvoucher'),
    path('dashboard/payable-voucher/<int:pk>/pdf/', accounting_views.loan_voucher_pdf, name='loan_voucher_pdf'),
    
    
    path('dashboard/payable/exp/<int:pk>/', accounting_views.exp_loanvoucher, name='exp_loanvoucher'),


    ###   open balance voucher ###
    path('dashboard/openbalancevouchers/', accounting_views.openbalance_voucher_list, name='openbalance_voucher_list'),
    path('dashboard/openbalancevouchers/add/', accounting_views.add_openbalance_voucher, name='add_openbalance_voucher'),
    path('dashboard/openbalancevouchers/edit/<int:pk>/', accounting_views.edit_openbalance_voucher, name='edit_openbalance_voucher'),
    path('dashboard/openbalancevouchers/delete/<int:pk>/', accounting_views.delete_openbalance_voucher, name='delete_openbalance_voucher'),
    path('dashboard/open-balance-voucher/<int:pk>/pdf/', accounting_views.openbalance_voucher_pdf, name='openbalance_voucher_pdf'),
    
    ## Project Ledger - 
    path('dashboard/project-ledger-voucher/', accounting_views.project_ledger_list, name='project_ledger_list'),
    path('dashboard/project-ledger-manage/', accounting_views.project_ledger_manage, name='project_ledger_manage'),
    path('dashboard/project-ledger-report/', accounting_views.project_ledger_report, name='project_ledger_report'),
    path('dashboard/project-ledger-report/pdf/', accounting_views.project_ledger_manage_pdf, name='project_ledger_manage_pdf'),
    
    
    
    
    ## Profit Ledger - 
    path('dashboard/profit-ledger-voucher/', accounting_views.profit_ledger_list, name='profit_ledger_list'),
    path('dashboard/profit-ledger-manage/', accounting_views.profit_ledger_manage, name='profit_ledger_manage'),
    path('dashboard/profit-ledger-report/', accounting_views.profit_ledger_report, name='profit_ledger_report'),
    path('dashboard/profit-ledger-report/pdf/', accounting_views.profit_ledger_manage_pdf, name='profit_ledger_manage_pdf'),
    
    path("dashboard/profit-shareamount-voucher/", accounting_views.profit_shareamount_list, name="profit_shareamount_list"),

    
    ## firebase --url ---
    path("save-fcm-token/", purchase_view.save_fcm_token, name="save_fcm_token"),

    
    ###  Expense Head ###
    path('dashboard/head-of-expense/', purchase_view.expense_head_list, name='expense_head_list'),
    path('dashboard/head-of-expense/add/', purchase_view.add_head_of_expense, name='add_head_of_expense'),
    path('dashboard/head-of-expense/edit/<int:pk>/', purchase_view.edit_head_of_expense, name='edit_head_of_expense'),
    path('dashboard/head-of-expense/delete/<int:pk>/', purchase_view.delete_head_of_expense, name='delete_head_of_expense'),
    path('dashboard/head-of-expense/update/<int:pk>/', purchase_view.update_expense_requisition, name='update_expense_requisition'),
    
    ###  Expense list ###    
    path('dashboard/expense/list', purchase_view.expense_list, name='expense_list'),
    path('dashboard/expense/add/', purchase_view.expense_add, name='expense_add'),
    path('dashboard/expense/edit/<int:pk>/', purchase_view.expense_edit, name='expense_edit'),
    path('dashboard/expense/delete/<int:pk>/', purchase_view.expense_delete, name='expense_delete'),
    path('dashboard/expense/Details/<int:pk>/', purchase_view.expense_voucher_pdf, name='expense_voucher_pdf'), 
    path('dashboard/expense-confirmation/', purchase_view.expense_list, name='expense_confirmation'),
    path('dashboard/expense-item-summary/', purchase_view.expense_item_summary, name='expense_item_summary'),
    path('dashboard/expense-admin-confirmation/<int:pk>/', purchase_view.expense_admin_confirm, name='expense_admin_confirm'),
    
    
    path('dashboard/expense/requisition/list', purchase_view.expense_requisition_list, name='expense_requisition_list'),
    path('dashboard/expense-requisition/edit/<int:pk>/', purchase_view.edit_expense_requisition, name='edit_expense_requisition'),
    path('dashboard/expense/requisition/delete/<int:pk>/', purchase_view.delete_expense_requisition, name='delete_expense_requisition'),
    path('dashboard/expense/requisitions/add', purchase_view.expense_requisition_add, name='expense_requisition_add'),
    path('dashboard/expense/confirmation', purchase_view.expense_requisition_confirmation, name='expense_requisition_confirmation'),
    path('dashboard/approve-expense-voucher/<int:pk>/', purchase_view.approve_expense_voucher, name='approve_expense_voucher'),
    ###  toh id ### 
    path('dashboard/expense/requisition/', purchase_view.grouped_requisitions_view, name='grouped_requisitions'),
    path('dashboard/expense/requisition/details/<str:date_str>/<int:project_id>/', purchase_view.requisition_details_view, name='requisition_details'),
    
    
    path('dashboard/expense/requisition/approve/', purchase_view.approve_selected_requisitions, name='approve_selected_requisitions'),
    path('dashboard/expense/requisition/data/print/<str:date_str>/<int:project_id>/', purchase_view.print_exp_requisition_data, name='print_exp_requisition_data'),



    ###  HRM Module ### 
    path('login/user-profile/', hrm_view.user_profile, name='user_profile'),
    
    path('attendance/public/btp-office/', hrm_view.public_attendance_hrm, name='public_attendance_hrm'),
    path('attendance/manage-access/btp-office/', hrm_view.manage_attendance_access_hrm, name='manage_attendance_access_hrm'),
    # path(
    #     "attendance/public/project/permission/",
    #     hrm_view.public_permission_project,
    #     name="public_permission_project",
    # ),
    
    path("attendance/public/project/check/attendance/", hrm_view.public_attendance_hrm_check, name="public_attendance_hrm_check"),
        
    path('dashboard/profile/', hrm_view.profile, name='profile'),
    path('dashboard/start-break/', hrm_view.start_break, name='start_break'),
    path('dashboard/end-break/', hrm_view.end_break, name='end_break'),
    path('dashboard/break-history/', hrm_view.break_history, name='break_history'),
    
    
    path('dashboard/employee/list', hrm_view.employee_list, name='employee_list'),
    path('dashboard/employee/details', hrm_view.employee_details, name='employee_details'),
    path('dashboard/employee/project/details/', hrm_view.employee_project_detail, name='employee_project_detail'),
    
    #path('dashboard/employee/add/', hrm_view.employee_add, name='employee_add'),
    path('dashboard/employee/edit/<int:pk>/', hrm_view.employee_edit, name='employee_edit'),
    path('dashboard/employee-user/edit/<int:pk>/', hrm_view.employee_edit_user, name='employee_edit_user'),
    path('dashboard/employee/delete/<int:pk>/', hrm_view.employee_delete, name='employee_delete'),
    path('dashboard/employee/details/<int:pk>/', hrm_view.employee_detail, name='employee_detail'),
    

    path('dashboard/employee-new/add/', hrm_view.add_employee, name='add_employee'),
    path('dashboard/monthly-salary-report/', hrm_view.monthly_salary_generate, name='monthly_salary_generate'),
    path('dashboard/monthly-salary-report/check/', hrm_view.monthly_salary_check, name='monthly_salary_check'),
    path("approve/<int:project_id>/<str:month_name>/", hrm_view.approve_salary_generate, name="approve_salary_generate"),
    
    
    ##RDA Employee -- 
    path('dashboard/rda/employees/', hrm_view.rda_employee_list, name='rda_employee_list'),
    path('dashboard/rda/employees/toggle/<int:pk>/', hrm_view.rda_employee_toggle_status, name='rda_employee_toggle_status'),
    path('dashboard/rda/employees/add/', hrm_view.rda_employee_add, name='rda_employee_add'),
    path('dashboard/rda/employees/<int:pk>/edit/', hrm_view.rda_employee_edit, name='rda_employee_edit'),
    path('dashboard/rda/employees/delete/<int:pk>/', hrm_view.rda_employee_delete, name='rda_employee_delete'),
    
    # Attendance URLs
    path('dashboard/attendance/', hrm_view.attendance_list, name='attendance_list'),
    path('dashboard/attendance/add/', hrm_view.attendance_create, name='attendance_add'),
    path('dashboard/attendance/edit/<int:pk>/', hrm_view.attendance_edit, name='attendance_edit'),
    path('dashboard/attendance/delete/<int:pk>/', hrm_view.attendance_delete, name='attendance_delete'),
    path('dashboard/attendance-summary/', hrm_view.employee_attendance_summary, name='employee_attendance_summary'),
    
    path('attendance/add-holiday/', hrm_view.attendance_add_holiday, name='attendance_add_holiday'),

    
    
    path('dashboard/attendance/<int:pk>/checkout-update/', hrm_view.AttendanceCheckoutUpdateView, name='attendance_checkout_update'),
    
    path('dashboard/attendance/upload/', hrm_view.attendance_upload_csv, name='attendance_upload_csv'),
    
    path('download-sample-csv/', hrm_view.download_sample_attendance_csv, name='download_sample_csv'),
    path('generate-attendance/', hrm_view.generate_attendance_records, name='generate_attendance'),

    # Payroll URLs
    path('dashboard/payroll/', hrm_view.payroll_list, name='payroll_list'),
    path('dashboard/payroll/print/', hrm_view.payroll_print, name='payroll_print'),
    path('update-pay-salary/', hrm_view.update_pay_salary, name='update_pay_salary'),
    path('dashboard/payroll/print/manual/', hrm_view.payroll_print_manual, name='payroll_print_manual'),

    # Payslip URLs
    path('dashboard/payslip/print/', hrm_view.payslip_print, name='payslip_print'),

    # Advance Payment URLs
    path('dashboard/advance/', hrm_view.advance_list, name='advance_list'),
    path('dashboard/advance/add/', hrm_view.advance_create, name='advance_add'),
    path('dashboard/advance/edit/<int:pk>/', hrm_view.advance_edit, name='advance_edit'),
    path('dashboard/advance/delete/<int:pk>/', hrm_view.advance_delete, name='advance_delete'),
    
    
    # Loan Payment URLs
    path('dashboard/loan/', hrm_view.loanPayment_list, name='loanPayment_list'),
    path('dashboard/loan/add/', hrm_view.loanPayment_add, name='loanPayment_add'),
    path('dashboard/loan/edit/<int:pk>/', hrm_view.loanpayment_edit, name='loanpayment_edit'),
    path('dashboard/loan/delete/<int:pk>/', hrm_view.loanpayment_delete, name='loanpayment_delete'),
    
    

    # Allowances Payment URLs
    path('dashboard/allowances/', hrm_view.allowances_list, name='allowances_list'),
    path('dashboard/allowances/add/', hrm_view.allowances_create, name='allowances_create'),
    path('dashboard/allowances/edit/<int:pk>/', hrm_view.allowances_edit, name='allowances_edit'),
    path('dashboard/allowances/delete/<int:pk>/', hrm_view.allowances_delete, name='allowances_delete'),
    
    
    # Allowances Payment URLs
    path('dashboard/salary/', hrm_view.salary_list, name='salary_list'),
    path('dashboard/salary/add/', hrm_view.salary_create, name='salary_create'),
    path('dashboard/salary/edit/<int:pk>/', hrm_view.salary_edit, name='salary_edit'),
    path('dashboard/salary/delete/<int:pk>/', hrm_view.salary_delete, name='salary_delete'),
    path('ajax/get-project-employees/', hrm_view.get_project_employees, name='get_project_employees'),
    
    
    # Leave URLs
    path('dashboard/leave/', hrm_view.leave_list, name='leave_list'),
    path('dashboard/leave/apply/', hrm_view.leave_apply, name='leave_apply'),
    path('dashboard/leave/edit/<int:pk>/', hrm_view.leave_edit, name='leave_edit'),
    path('dashboard/leave/delete/<int:pk>/', hrm_view.leave_delete, name='leave_delete'),
    #path('dashboard/leave-summary/', hrm_view.employee_leave_summary, name='employee_leave_summary'),
    path('dashboard/approval/<int:pk>/', hrm_view.leave_approval, name='leave_approval'),
    
    
    path('dashboard/leave-summary/', hrm_view.employee_leave_summary, name='employee_leave_summary'),

    # Leave Allocation CRUD
    path('dashboard/leave/allocations/', hrm_view.allocation_list, name='allocation_list'),
    path('dashboard/leave/allocations/create/', hrm_view.allocation_create, name='allocation_create'),
    path('dashboard/leave/allocations/edit/<int:pk>/', hrm_view.allocation_edit, name='allocation_edit'),
    path('dashboard/leave/allocations/delete/<int:pk>/', hrm_view.allocation_delete, name='allocation_delete'),
    
    
    # IOM URLs
    path('dashboard/iom/', hrm_view.iom_list, name='iom_list'),
    path('dashboard/iom/apply/', hrm_view.iom_apply, name='iom_apply'),
    path('dashboard/iom/edit/<int:pk>/', hrm_view.iom_edit, name='iom_edit'),
    path('dashboard/iom/delete/<int:pk>/', hrm_view.iom_delete, name='iom_delete'),
    path('dashboard/iom-summary/', hrm_view.employee_iom_summary, name='employee_iom_summary'),
    path('dashboard/iom/approval/<int:pk>/', hrm_view.iom_approval, name='iom_approval'),
    
    #path("get-attendance/", hrm_view.get_attendance, name="get_attendance"),
    
    
    # Note URLs
    path('dashboard/note/', hrm_view.note_list, name='note_list'),
    path('dashboard/note/apply/', hrm_view.note_apply, name='note_apply'),
    path('dashboard/note/edit/<int:pk>/', hrm_view.note_edit, name='note_edit'),
    path('dashboard/note/delete/<int:pk>/', hrm_view.note_delete, name='note_delete'),
    path('dashboard/note/details/<int:pk>/', hrm_view.note_details, name='note_details'),
    path('dashboard/attendance/note/<int:employee_id>/', hrm_view.attendance_note, name='attendance_note'),

    ## permissions edit ---
    path('dashboard/users-permissions/list', hrm_view.user_permissions_list, name='user_permissions_list'),
    path('dashboard/users-permissions/<int:user_id>/permissions/', hrm_view.edit_user_permissions, name='edit_user_permissions'),
    # path("dashboard/iclock/cdata", hrm_view.iclock_cdata, name='edit_user_permissions'),  

    ###  Requisitions App Module ###
    path('dashboard/requisitions/', purchase_view.requisitions_create, name='requisitions_create'),
    path('dashboard/requisitions/list/', purchase_view.requisition_list, name='requisition_list'),
    #path('dashboard/requisitions/project/<int:project_id>/', purchase_view.requisition_by_project, name='requisition_by_project'),
    
    path('requisition/by-project/<int:requi_id>/', purchase_view.requisition_by_project, name='requisition_by_project'),
    path('requisition/requisitions/by-details/<int:project_id>/', purchase_view.requisition_by_fallback, name='requisition_by_fallback'),

    path('dashboard/requisitions/edit/<int:pk>/', purchase_view.requisition_edit, name='requisition_edit'),
    path('dashboard/requisitions/delete/<int:pk>/', purchase_view.requisition_delete, name='requisition_delete'), 
        
    path('dashboard/project-boq-requisition-summary/', purchase_view.project_boq_requisition_summary, name='project_boq_requisition_summary'),

    path("get-stock-qty/", purchase_view.get_stock_qty, name="get_stock_qty"),
    
    
    path('dashboard/bill/requisitions/list/', purchase_view.bill_requisition_list, name='bill_requisition_list'),
    path('dashboard/bill/requisitions/create', purchase_view.bill_requisitions_create, name='bill_requisitions_create'),
    path('dashboard/bill/requisitions/confirmation/', purchase_view.bill_requisition_confirmation, name='bill_requisition_confirmation'),
    path('bill_requisition_update_ajax/', purchase_view.bill_requisition_update_ajax, name='bill_requisition_update_ajax'),
    path('requisition/bill/by-project/<int:requi_id>/', purchase_view.bill_requisition_by_project, name='bill_requisition_by_project'),
    path('requisition/bill/requisitions/by-details/<int:project_id>/', purchase_view.bill_requisition_by_fallback, name='bill_requisition_by_fallback'),
    path('dashboard/bill/requisitions/edit/<int:pk>/', purchase_view.bill_requisition_edit, name='bill_requisition_edit'),
    path('dashboard/bill/requisitions/delete/<int:pk>/', purchase_view.bill_requisition_delete, name='bill_requisition_delete'), 
    path('dashboard/bill/requisition-item-summary/', purchase_view.bill_requisition_item_summary, name='bill_requisition_item_summary'),
       
     ###  Petty Cash List ###
    path('dashboard/pettycash/', purchase_view.pettycash_create, name='pettycash_create'),
    path('dashboard/pettycash/list/', purchase_view.petty_cash_list, name='petty_cash_list'),
    path('dashboard/pettycash/edit/<int:pk>/', purchase_view.pettycash_edit, name='pettycash_edit'),
    path('dashboard/pettycash-details/<int:pk>/', purchase_view.pettycash_detail, name='pettycash_detail'),
    path('dashboard/pettycash/delete/<int:pk>/', purchase_view.pettycash_delete, name='pettycash_delete'), 
        
    path('dashboard/project-boq-requisition-summary/', purchase_view.project_boq_requisition_summary, name='project_boq_requisition_summary'),
    path('dashboard/pettycash-item-summary/', purchase_view.pettycash_item_summary, name='pettycash_item_summary'),
    path('dashboard/pettycash-acct-confirmation/', purchase_view.pettycash_acct_confirmation, name='pettycash_acct_confirmation'),
    path('dashboard/pettycash-admin-confirmation/', purchase_view.admin_confirmation, name='admin_confirmation'),


    ###  Requisition Category ###
    path('dashboard/requisition-category/', purchase_view.requisition_category, name='requisition_category'),
    path('dashboard/requisition-category/add/', purchase_view.add_requisition_category, name='add_requisition_category'),
    path('dashboard/requisition-category/edit/<int:pk>/', purchase_view.requisition_category_edit, name='requisition_category_edit'),
    path('dashboard/requisition-category/delete/<int:pk>/', purchase_view.requisition_category_delete, name='requisition_category_delete'),
    
    ###  Requisition Head ###
    path('dashboard/head-of-requisition/', purchase_view.head_of_requisition_list, name='head_of_requisition_list'),
    path('dashboard/head-of-requisition/add/', purchase_view.add_head_of_requisition, name='add_head_of_requisition'),
    path('dashboard/head-of-requisition/edit/<int:pk>/', purchase_view.edit_head_of_requisition, name='edit_head_of_requisition'),
    path('dashboard/head-of-requisition/delete/<int:pk>/', purchase_view.delete_head_of_requisition, name='delete_head_of_requisition'),
    
    path("dashboard/head-of-requisition/pdf/", purchase_view.head_of_requisition_pdf, name="head_of_requisition_pdf"),
    
     ###  Requisition Comparative ###
    path('dashboard/requisition-comparative/', purchase_view.requisition_comparative_list, name='requisition_comparative_list'),
    path('dashboard/requisition-comparative/add/', purchase_view.add_requisition_comparative, name='add_requisition_comparative'),
    path('dashboard/requisition-comparative-approval/', purchase_view.requis_comparative_approval, name='requis_comparative_approval'),
    path('dashboard/requisition-comparative-check/', purchase_view.requis_comparative_check, name='requis_comparative_check'),
    path('dashboard/requisitions-comparative/edit/<int:pk>/', purchase_view.requisition_comparative_edit, name='requisition_comparative_edit'),
    path('dashboard/requisitions-comparative/delete/<int:pk>/', purchase_view.requisition_comparative_delete, name='requisition_comparative_delete'), 
    path('dashboard/requisition-comparative-admin-confirmation/<int:pk>/', purchase_view.requisition_comparative_admin_confirm, name='requisition_comparative_admin_confirm'),
    
    path('dashboard/requisition-invoice/list/', purchase_view.requisition_invoice_list, name='requisition_invoice_list'),
    path('dashboard/requisition-invoice-details/<int:pk>/', purchase_view.requisition_invoice_details, name='requisition_invoice_details'),
    # ... other urls
    

    ###  Purchase Module ###
    path('dashboard/requisition-approv-list/list/', purchase_view.requisition_approv_list, name='requisition_approv_list'),
    path('dashboard/purchase/details/<int:requi_id>/<int:purch_id>/', purchase_view.purchase_check_details, name='purchase_check_details'),
    path('dashboard/purchase/approval/action/<int:requi_id>/<int:purch_id>/', purchase_view.purchase_approval_action, name='purchase_approval_action'),
    path('dashboard/purchase/repurchase/<int:requi_id>/<str:purch_id>/', purchase_view.purchase_repurchase, name='purchase_repurchase'),
    path('dashboard/purchase/repurchase/save/<int:requi_id>/', purchase_view.purchase_repurchase_save, name='purchase_repurchase_save'),

    path('dashboard/purchase/list/', purchase_view.purchase_list, name='purchase_list'),
    path('dashboard/purchase-cash-details/<int:pk>/', purchase_view.purchase_cash_details, name='purchase_cash_details'),

    path('dashboard/purchase-order/list/', purchase_view.purchase_order_list, name='purchase_order_list'),
    path('dashboard/purchase-orderss-details/<int:pk>/', purchase_view.purchase_order_details, name='purchase_order_details'),
    
    path('dashboard/purchase-invoice/list/', purchase_view.purchase_invoice_list, name='purchase_invoice_list'),
    path('dashboard/purchase-invoice-details/<int:pk>/', purchase_view.purchase_invoice_details, name='purchase_invoice_details'),
    
    path('dashboard/purchase-invoice-details/update-amount/', purchase_view.update_amount, name='update_amount'),
    
    path('dashboard/purchase-invoice/filter/', purchase_view.purchase_invoice_filter, name='purchase_invoice_filter'),
    path('dashboard/purchase-invoice-filter-details/<int:pk>/', purchase_view.purchase_invoice_filter_details, name='purchase_invoice_filter_details'),

    # urls.py
    path('dashboard/update-files/<int:purch_id>/<int:file_index>/', purchase_view.update_purch_file, name='update_purch_file'),


    path('dashboard/requisition-confirmation/', purchase_view.requisition_confirmation, name='requisition_confirmation'),
    path('dashboard/requisition-details/<int:pk>/', purchase_view.requisition_detail, name='requisition_detail'),
    
    path('dashboard/requisition-item-details/<int:pk>/', purchase_view.requisition_item_detail, name='requisition_item_detail'),
    
    path('requisition_update_ajax/', purchase_view.requisition_update_ajax, name='requisition_update_ajax'),

    path('dashboard/requisition-item-summary/', purchase_view.requisition_item_summary, name='requisition_item_summary'),
    
    path('dashboard/bill/requisition/payments/', purchase_view.bill_reqs_payment_list, name='bill_reqs_payment_list'),
    path('dashboard/requi-app-pay-pdf/bill/<int:contractor_id>/', purchase_view.bill_requi_app_pay_pdf, name='bill_requi_app_pay_pdf'),
    path('dashboard/approval/payment/edit/bill<int:pk>/', purchase_view.bill_approval_payment_edit, name='bill_approval_payment_edit'),
    path('dashboard/approval/payment/delete/bill/<int:pk>/', purchase_view.bill_approval_payment_delete, name='bill_approval_payment_delete'),
    
    
    path('dashboard/requisition/payments/', purchase_view.requisition_payment_list, name='requisition_payment_list'),
    path('dashboard/requi-app-pay-pdf/<int:supplier_id>/', purchase_view.requi_app_pay_pdf, name='requi_app_pay_pdf'),
    
    # Approval
    path('dashboard/approval/payment/edit/<int:pk>/', purchase_view.approval_payment_edit, name='approval_payment_edit'),
    path('dashboard/approval/payment/delete/<int:pk>/', purchase_view.approval_payment_delete, name='approval_payment_delete'),

    path('dashboard/supplier-payment/add/<int:id>/', accounting_views.requi_supplier_payment, name='requi_supplier_payment'),

    path('dashboard/return-purchase/list/', purchase_view.return_purchase_list, name='return_purchase_list'),
    path('dashboard/approve-return-purchase/<int:pk>/', purchase_view.approve_return_voucher, name='approve_return_voucher'),
    path('dashboard/return-purchase/item/', purchase_view.return_purchase_item, name='return_purchase_item'),
    path('dashboard/return-items/', purchase_view.return_item_list, name='return_item_list'),

    ## Notification --
    path('dashboard/notifications/', purchase_view.notifications_list, name='notifications_list'),
    path('dashboard/notifications/mark-read/<int:pk>/', purchase_view.mark_notification_read, name='mark_notification_read'),
    path('dashboard/notification/read/<int:pk>/', purchase_view.read_notification, name='read_notification'),

    path('dashboard/requisition-admin-confirmation/<int:pk>/', purchase_view.requisition_admin_confirm, name='requisition_admin_confirm'),
    path('dashboard/requisition-acct-confirmation/', purchase_view.requisition_acct_confirmation, name='requisition_acct_confirmation'),
    path('dashboard/requisition-acct-confirmation/', purchase_view.requisition_acct_confirmation, name='requisition_accounts_confirm'),
    
    ## Inventory --
    path('dashboard/inventory-item-list/', inventories_view.inventory_item_list, name='inventory_item_list'), 
    path('dashboard/inventory-item/details/<int:pk>/', inventories_view.inventory_item_detail, name='inventory_item_detail'),
    path('dashboard/inventory-item-summary/', inventories_view.inventory_item_summary, name='inventory_item_summary'),

    
    ## Inventory Stock Summary --
    path('dashboard/inventory-stock-summary/', inventories_view.inventory_stock_summary, name='inventory_stock_summary'),
    path('dashboard/inventory-item-summary-check/', inventories_view.inventory_stock_summary_check, name='inventory_stock_summary_check'),
    path('dashboard/inventory-use/create/', inventories_view.inventory_use_create, name='inventory_use_create'),
    path('dashboard/inventory-use/list/', inventories_view.inventory_use_list, name='inventory_use_list'),
    path('dashboard/inventory-use-item-summary/', inventories_view.use_item_summary, name='use_item_summary'),
    path('dashboard/inventory-use-edit/<int:id>/', inventories_view.inventory_use_edit, name='inventory_use_edit'),
    
    path('dashboard/update-inventory/', inventories_view.update_inventory_ajax, name='update_inventory_ajax'),
    
    path(
        'inventory-transfer/',
        inventories_view.inventory_stock_item_transfer,
        name='inventory_stock_item_transfer'
    ),

    path(
        'get-project-items/<int:project_id>/',
        inventories_view.get_project_items,
        name='get_project_items'
    ),
    
    path('get-project-wise-items/', inventories_view.get_project_wise_items, name='get_project_wise_items'),
    
    
    
  
     ## Inventory Ledger - 
    path('dashboard/inv-stock-ledger-voucher/', accounting_views.invStock_ledger_list, name='invStock_ledger_list'),
    path('dashboard/inv-stock-ledger-manage/', accounting_views.invStock_ledger_manage, name='invStock_ledger_manage'),
    path('dashboard/inv-stock-ledger-report/', accounting_views.invStock_ledger_report, name='invStock_ledger_report'),
    path('dashboard/inv-stock-ledger-report/pdf/', accounting_views.invStock_ledger_manage_pdf, name='invStock_ledger_manage_pdf'),

 

    
    ###   Ledger Reports module ###
    path('dashboard/report-manage/list', accounting_views.reports_manage_list, name='reports_manage_list'),
    path('dashboard/ledger-manage', accounting_views.ledger_manage, name='ledger_manage'),
    path('dashboard/ledger-report', accounting_views.ledger_report, name='ledger_report'),
    path('dashboard/ledger-report-pdf/print/', accounting_views.ledger_manage_pdf, name='ledger_manage_pdf'),


    ###   Bank Reports module ###
    path('dashboard/bank-report-manage/list', accounting_views.bank_reports_list, name='bank_reports_list'),
    path('dashboard/bank-report-manage', accounting_views.bank_ledger_manage, name='bank_ledger_manage'),
    path('dashboard/bank-report', accounting_views.bank_ledger_report, name='bank_ledger_report'),
    path('dashboard/bank-report-pdf/print/', accounting_views.bank_ledger_manage_pdf, name='bank_ledger_manage_pdf'),


    ###  Transaction Reports module ###
    path('dashboard/transaction-report-manage/list', accounting_views.transaction_reports_list, name='transaction_reports_list'),
    path('dashboard/transaction-report-manage', accounting_views.transaction_ledger_manage, name='transaction_ledger_manage'),
    path('dashboard/transaction-ledger-report', accounting_views.transaction_ledger_report, name='transaction_ledger_report'),
    path('dashboard/transaction-report-pdf/print/', accounting_views.transaction_ledger_manage_pdf, name='transaction_ledger_manage_pdf'),

    ###  Top Sheet Reports module ###
    path('dashboard/topsheet-report-manage/list', accounting_views.topsheet_reports_list, name='topsheet_reports_list'),
    path('dashboard/topsheet-report-manage', accounting_views.topsheet_ledger_manage, name='topsheet_ledger_manage'),
    path('dashboard/topsheet-report', accounting_views.topsheet_ledger_report, name='topsheet_ledger_report'),
    path('dashboard/topsheet-report-pdf/print/', accounting_views.topsheet_ledger_manage_pdf, name='topsheet_ledger_manage_pdf'),

    ###   Bank Reports module ###
    path('dashboard/monthly-collection-report-manage/list', accounting_views.monthly_collection_reports_list, name='monthly_collection_reports_list'),
    path('dashboard/monthly-collection-report-manage', accounting_views.monthly_collection_manage, name='monthly_collection_manage'),
    path('dashboard/monthly-collection-report', accounting_views.monthly_collection_report, name='monthly_collection_report'),
    path('dashboard/monthly-collection-report-pdf/print/', accounting_views.monthly_collection_manage_pdf, name='monthly_collection_manage_pdf'),

    ###   Bank Reconciliation module ###
    path('dashboard/upload-statement/', accounting_views.upload_statement, name='upload_statement'),
    path('dashboard/reconciliation/', accounting_views.reconciliation_dashboard, name='reconciliation_dashboard'),
    path('dashboard/reconciliation/<int:bank_id>/create/', accounting_views.reconciliation_create, name='reconciliation_create'),
    path('dashboard/reconciliation/<int:bank_id>/list', accounting_views.reconciliation_list, name='reconciliation_list'), 
    path('dashboard/reconciliation/<int:bank_id>/report/', accounting_views.reconciliation_report, name='reconciliation_report'),


    ###   Supplier Ledger Reports module ###
    path('dashboard/supplier-report-manage/list', accounting_views.supplier_reports_manage_list, name='supplier_reports_manage_list'),
    path('dashboard/supplier-ledger-manage-sup', accounting_views.supplier_ledger_manage, name='supplier_ledger_manage'),
    path('dashboard/supplier-ledger-report-sup', accounting_views.supplier_ledger_report, name='supplier_ledger_report'),
    path('dashboard/supplier-ledger-report-sup-pdf/print/', accounting_views.supplier_ledger_manage_pdf, name='supplier_ledger_manage_pdf'), 
    
    path('dashboard/ledger-sup-report/', accounting_views.ledger_sup_details, name='ledger_sup_details'),
    
    path('dashboard/supplier-summary/', accounting_views.supplier_summary_report, name='supplier_summary_report'),
    
    path('dashboard/employee-summary/', accounting_views.employee_summary_report, name='employee_summary_report'),
    path('dashboard/employee-ledger-manage', accounting_views.employee_ledger_manage, name='employee_ledger_manage'),
    path('dashboard/employee-ledger-report', accounting_views.employee_ledger_report, name='employee_ledger_report'),
    path('dashboard/employee-ledger-report-pdf/print/', accounting_views.employee_ledger_manage_pdf, name='employee_ledger_manage_pdf'),    
    
    ## Customer Ledger ---
    path('dashboard/customer-summary/list', accounting_views.customer_summary_report, name='customer_summary_report'),
    path('dashboard/customer-ledger-manage', accounting_views.customer_ledger_manage, name='customer_ledger_manage'),
    path('dashboard/customer-ledger-report', accounting_views.customer_ledger_report, name='customer_ledger_report'),
    path('dashboard/customer-ledger-report-pdf/print/', accounting_views.customer_ledger_manage_pdf, name='customer_ledger_manage_pdf'), 
    
    
    path('dashboard/purchase-summary/', accounting_views.purchase_summary_report, name='purchase_summary_report'),
    path('dashboard/purchase-ledger-manage', accounting_views.purchase_ledger_manage, name='purchase_ledger_manage'),
    path('dashboard/purchase-ledger-report/', accounting_views.purchase_ledger_report, name='purchase_ledger_report'),
    path('dashboard/purchase-ledger-report-pdf/print/', accounting_views.purchase_ledger_manage_pdf, name='purchase_ledger_manage_pdf'), 


    path('dashboard/capital-accounts/', accounting_views.capital_account_list, name='capital_account_list'),
    path('dashboard/capital-accounts/add/', accounting_views.capital_account_create, name='capital_account_add'),
    path('dashboard/capital-accounts/edit/<int:pk>/', accounting_views.capital_account_edit, name='capital_account_edit'),
    path('dashboard/capital-accounts/delete/<int:pk>/', accounting_views.capital_account_delete, name='capital_account_delete'),

    ## Genarel Ledger Ne urls--
    path('get-types-by-head/<int:head_id>/', accounting_views.get_types_by_head, name='get_types_by_head'),
    path('get-projects-by-head-cash/<int:head_id>/<int:cash_type_id>/', accounting_views.get_projects_by_head_cash, name='get_projects_by_head_cash'),
    
     ###  Sales List ###
    path('dashboard/flat-plot-summary', sales_view.flat_plot_summary, name='flat_plot_summary'),
    path('dashboard/flat-plot-add', sales_view.flat_plot_add, name='flat_plot_add'),
    path('dashboard/flat-plot-property-add', sales_view.flat_plot_property_add, name='flat_plot_property_add'),
    path('dashboard/flat-plot-property-list', sales_view.flat_plot_property_list, name='flat_plot_property_list'),
    
    path('dashboard/flatplots/project/<int:project_id>/', sales_view.flatplot_project_detail, name='flatplot_project_detail'),
    path('dashboard/flatplots/edit/<int:id>/', sales_view.flatplot_edit, name='flatplot_edit'),
    path('dashboard/flatplots/delete/<int:id>/', sales_view.flatplot_delete, name='flatplot_delete'),
    
    path('dashboard/property/edit/<int:id>/', sales_view.property_edit, name='property_edit'),
    path('dashboard/property/delete/<int:id>/', sales_view.property_delete, name='property_delete'),
    
    path('dashboard/flat-plot-sales', sales_view.flat_plot_sales, name='flat_plot_sales'),
    path('dashboard/flat-plot-sales/add', sales_view.flat_plot_sales_add, name='flat_plot_sales_add'),
    path('dashboard/flat-plot-sales/installment', sales_view.flat_plot_installment_management, name='flat_plot_installment_management'),
    path('dashboard/installments/<int:id>/', sales_view.installment_list, name='installment_list'),
    path('dashboard/installments/update-status/', sales_view.update_installment_status, name='update_installment_status'),
    path('dashboard/installments/summary/<int:id>/', sales_view.flat_plot_sales_summary, name='flat_plot_sales_summary'),
    
    path('dashboard/installment/invoice/<int:pk>/', sales_view.sales_payment_invoice, name='sales_payment_invoice'),
    path('dashboard/installment/edit/<int:pk>/', sales_view.installment_payment_edit, name='sales_payment_edit'),
    path('dashboard/installment/delete/<int:pk>/', sales_view.installment_payment_delete, name='sales_payment_delete'),
    
    
    path('dashboard/installments/property-sales/<int:id>/report/', sales_view.property_sales_report, name='property_sales_report'),
    path('dashboard/flat-plot-sales/edit/<int:sales_id>/', sales_view.edit_property_sale, name='property_sale_edit'),
    path('dashboard/flat-plot-sales/delete/<int:sales_id>/', sales_view.delete_property_sale, name='property_sale_delete'),
    
    path('dashboard/share-plot-list', sales_view.sharePlotList, name='share_plot_list'),
    path('dashboard/share-plot-add', sales_view.share_plot_add, name='share_plot_add'),
    path('dashboard/share-plot/<int:pk>/', sales_view.share_plot_pdf, name='share_plot_pdf'),
    path("dashboard/share-plot/<int:pk>/delete/", sales_view.delete_share_plot, name="delete_share_plot"),
    
    path('dashboard/share-plot-sales/installment', sales_view.share_installment_management, name='share_installment_management'),
    path('dashboard/share-installment-list', sales_view.share_installment_list, name='share_installment_list'),
    path("update-pay-status/", sales_view.update_pay_status, name="update_pay_status"),

    
    ###  Sales List ###
    path('dashboard/sales/list', sales_view.sales_list, name='sales_list'),
    path('dashboard/sales/add/', sales_view.sales_add, name='sales_add'),
    path('dashboard/sales/edit/<int:pk>/', sales_view.sales_edit, name='sales_edit'),
    path('dashboard/sales/delete/<int:pk>/', sales_view.sales_delete, name='sales_delete'),
    
    
    path('dashboard/sales-commission/list', sales_view.sales_commission_list, name='sales_commission_list'),
    
    path('dashboard/sales-lilahetalah/list', sales_view.sales_lilahetalah_list, name='sales_lilahetalah_list'),

    path('dashboard/deleted-records/', inventories_view.deleted_records_view, name='deleted_records'),
    path('dashboard/deleted-records/undo/<int:pk>/', inventories_view.undo_deleted_record, name='undo_deleted_record'),
    
    
    ###  Trail Balance Reports module ###
    path('dashboard/trailbalance-report-manage/list', accounting_views.trial_balance_list, name='trial_balance_list'),
    path('dashboard/trailbalance-report-manage', accounting_views.trial_balance_ledger_manage, name='trial_balance_ledger_manage'),
    path('dashboard/trailbalance-report', accounting_views.trial_balance_ledger_report, name='trial_balance_ledger_report'),
    path('dashboard/trailbalance-report-pdf/print/', accounting_views.trial_balance_ledger_manage_pdf, name='trial_balance_ledger_manage_pdf'),
    
    
    
    path('dashboard/balance-sheet-heads/', accounting_views.balance_sheet_head_list, name='balance_sheet_head_list'),
    path('dashboard/balance-sheet-head/add/', accounting_views.balance_sheet_head_add, name='balance_sheet_head_add'),
    path('dashboard/balance-sheet-head/edit/<int:id>/', accounting_views.balance_sheet_head_edit, name='balance_sheet_head_edit'),
    path('dashboard/balance-sheet-head/delete/<int:id>/', accounting_views.balance_sheet_head_delete, name='balance_sheet_head_delete'),


    path('dashboard/balance-items/list/', accounting_views.balance_item_list, name='balance_item_list'),
    path('dashboard/balance-items/create/', accounting_views.balance_item_create, name='balance_item_create'),
    path('dashboard/balance-sheet/report/', accounting_views.balance_sheet_report, name='balance_sheet_report'),
    path('dashboard/balance-sheet/check/', accounting_views.balance_sheet_check, name='balance_sheet_check'),


    path('dashboard/balance-item/edit/<int:pk>/', accounting_views.balance_item_edit, name='edit_balance_sheet'),
    path('dashboard/balance-item/delete/<int:pk>/', accounting_views.balance_item_delete, name='delete_balance_sheet'),
    path('dashboard/balance-item/details/<int:pk>/', accounting_views.balance_item_detail, name='balance_item_detail'),
    path('dashboard/balance-item/<int:pk>/approve/', accounting_views.approve_balance_item, name='approve_balance_item'),
    
    
    
    ##   RESTAURANT APP  Public access ##
    
    # ================= PUBLIC RESTAURANT SUPPLIER =================
    path('public/restaurant/requisitions/home',  restaurant_view.public_restaurant_home, name='public_restaurant_home'),
    
    path('public/restaurant-suppliers/list', restaurant_view.public_restaurant_supplier_list, name='public_restaurant_supplier_list'),

    path('public/restaurant-suppliers/add/', restaurant_view.public_add_restaurant_supplier, name='public_add_restaurant_supplier'),

    path('public/restaurant-suppliers/edit/<int:pk>/', restaurant_view.public_edit_restaurant_supplier, name='public_edit_restaurant_supplier'),

    path('public/restaurant-suppliers/delete/<int:pk>/', restaurant_view.public_delete_restaurant_supplier, name='public_delete_restaurant_supplier'),
    
    
    path('public/restaurant/expense/account/list/', restaurant_view.restaurant_expense_account_list, name='restaurant_expense_account_list'),
    
    
    # ================= PUBLIC EXPENSE =================
    path('public/restaurant-category/exp/list', restaurant_view.public_restaurant_requisition_exp_category, name='public_restaurant_requisition_exp_category'),
    
    path('public/restaurant-category/add/exp/', restaurant_view.public_add_restaurant_exp_category, name='public_add_restaurant_exp_category'),
    
    path('public/restaurant-category/edit/exp/<int:pk>/', restaurant_view.public_restaurant_exp_category_edit, name='public_restaurant_exp_category_edit'),

    path('public/restaurant-category/delete/exp/<int:pk>/', restaurant_view.public_restaurant_exp_category_delete, name='public_restaurant_exp_category_delete'),
    
    
    
    path('public/restaurant/expense/list/', restaurant_view.restaurant_expense_public_list, name='restaurant_expense_public_list'),

    path('public/restaurant/expense/add/', restaurant_view.add_restaurant_expense_public, name='add_restaurant_expense_public'),

    path('public/restaurant/expense/edit/<int:pk>/', restaurant_view.edit_restaurant_expense_public, name='edit_restaurant_expense_public'),

    path('public/restaurant/expense/delete/<int:pk>/', restaurant_view.delete_restaurant_expense_public, name='delete_restaurant_expense_public'),
    
    
    # ================= PUBLIC CATEGORY =================
    path('public/restaurant-category/list', restaurant_view.public_restaurant_category, name='public_restaurant_requisition_category'),

    path('public/restaurant-category/add/', restaurant_view.public_add_restaurant_category, name='public_add_restaurant_category'),

    path('public/restaurant-category/edit/<int:pk>/', restaurant_view.public_restaurant_category_edit, name='public_restaurant_category_edit'),

    path('public/restaurant-category/delete/<int:pk>/', restaurant_view.public_restaurant_category_delete, name='public_restaurant_category_delete'),
    
     # ================= PUBLIC Item Name =================
    path('public/restaurant-items/', restaurant_view.public_restaurant_item_list, name='public_restaurant_item_name'),

    path('public/restaurant-items/add/', restaurant_view.public_add_restaurant_item, name='public_add_restaurant_item_name'),

    path('public/restaurant-items/edit/<int:pk>/', restaurant_view.public_edit_restaurant_item, name='public_edit_restaurant_item'),

    path('public/restaurant-items/delete/<int:pk>/', restaurant_view.public_delete_restaurant_item, name='public_delete_restaurant_item'),
    
    
    
    path('requisitions/public/store/list/', restaurant_view.restau_requisition_list_public_store, name='restau_requisition_list_public_store'),
    path('requisitions/public/store/bulk-approve/', restaurant_view.restau_requisition_bulk_approve, name='restau_requisition_bulk_approve'),

    path('requisition/restau/requisitions/by-details/public/store/<int:project_id>/', restaurant_view.restu_requisition_by_fallback_public_store, name='restu_requisition_by_fallback_public_store'),
    path('requisition/restau/update-purch-status/', restaurant_view.update_purch_status_ajax, name='update_purch_status_ajax'),
    path('requisition/restau/requisitions/edit/public/store/<int:pk>/', restaurant_view.restau_requisition_edit_public_store, name='restau_requisition_edit_public_store'),
    path('requisition/restau/requisitions/delete/public/store/<int:pk>/', restaurant_view.restau_requisition_delete_public_store, name='restau_requisition_delete_public_store'),
    
    
    path('requisitions/public/list/', restaurant_view.restau_requisition_list_public, name='restau_requisition_list_public'),
    path('requisitions/public/history/', restaurant_view.restaurant_expense_purchase_history, name='restaurant_expense_purchase_history'),
    path('requisitions/public/update-inline/', restaurant_view.update_inline_requisition, name='update_inline_requisition'),
    path('requisition/restau/requisitions/by-details/public/<int:project_id>/', restaurant_view.restu_requisition_by_fallback_public, name='restu_requisition_by_fallback_public'),
    path('requisition/restau/requisitions/edit/public/<int:pk>/', restaurant_view.restau_requisition_edit_public, name='restau_requisition_edit_public'),
    path('requisition/restau/requisitions/delete/public/<int:pk>/', restaurant_view.restau_requisition_delete_public, name='restau_requisition_delete_public'),
    
    path('requisitions/public/list/purchase', restaurant_view.requisition_jewel_purchase_list, name='requisition_jewel_purchase_list'),
    path('requisitions/purchase/edit/<str:purch_appov>/', restaurant_view.edit_purch_requisition_jewel, name='edit_purch_requisition_jewel'),
    path('restaurant/kitchen-ledger/', restaurant_view.restaurant_kitchen_ledger_list, name='restaurant_kitchen_ledger_list'),
    path('restaurant/kitchen-ledger/view/<int:project_id>/', restaurant_view.restaurant_kitchen_ledger_view, name='restaurant_kitchen_ledger_view'),
    
    
    path('requisitions/inventory/project-wise/', restaurant_view.rest_inventory_project_wise, name='rest_inventory_project_wise'),
    path('requisitions/inventory/project-wise/<int:project_id>/', restaurant_view.rest_inventory_project_wise, name='rest_inventory_project_wise_filtered'),
    path('requisitions/inventory/deduct/<int:inventory_id>/', restaurant_view.requisition_deduct_inventory_stock, name='requisition_deduct_inventory_stock'),
    
    
    # path('requisitions/approval-ranges/', restaurant_view.approval_range_list, name='approval_range_list'),
    # path('requisitions/approval-ranges/create/', restaurant_view.approval_range_create, name='approval_range_create'),
    # path('requisitions/approval-ranges/<int:pk>/edit/', restaurant_view.approval_range_edit, name='approval_range_edit'),
    # path('requisitions/approval-ranges/<int:pk>/delete/', restaurant_view.approval_range_delete, name='approval_range_delete'),

    # # Restaurant Budget URLs
    # path('requisitions/budgets/', restaurant_view.budget_list, name='budget_list'),
    # path('requisitions/budgets/create/', restaurant_view.budget_create, name='budget_create'),
    # path('requisitions/budgets/<int:pk>/edit/', restaurant_view.budget_edit, name='budget_edit'),
    # path('requisitions/budgets/<int:pk>/delete/', restaurant_view.budget_delete, name='budget_delete'),
    
    
    ##   RESTAURANT APP  Private ##
    
    path('dashboard/restaurant-expense/requisition/list', restaurant_view.restaurant_grouped_requisitions, name='restaurant_grouped_requisitions'),
    path('dashboard/restaurant-expense/requisitions/add', restaurant_view.restaurant_expense_requisition_add, name='restaurant_expense_requisition_add'),
    path('dashboard/restaurant-expense/requisition/details/<str:date_str>/<int:project_id>/', restaurant_view.restaurant_requisition_details, name='restaurant_requisition_details'),
    path('dashboard/restaurant-expense-requisition/edit/<int:pk>/', restaurant_view.rest_edit_expense_requisition, name='rest_edit_expense_requisition'),
    path('dashboard/restaurant-expense/requisition/delete/<int:pk>/', restaurant_view.rest_delete_expense_requisition, name='rest_delete_expense_requisition'),
    path('dashboard/restaurant-expense/requisition/approve/', restaurant_view.rest_approve_selected_requisitions, name='rest_approve_selected_requisitions'),
    path('dashboard/restaurant-expense/requisition/data/print/<str:date_str>/<int:project_id>/', restaurant_view.rest_print_exp_requisition_data, name='rest_print_exp_requisition_data'),
	
    
    path('dashboard/restaurant-expense/list', restaurant_view.rest_expense_list, name='rest_expense_list'),
    path('dashboard/restaurant-expense/add/', restaurant_view.rest_expense_add, name='rest_expense_add'),
    path('dashboard/restaurant-expense/edit/<int:pk>/', restaurant_view.rest_expense_edit, name='rest_expense_edit'),
    path('dashboard/restaurant-expense/delete/<int:pk>/', restaurant_view.rest_expense_delete, name='rest_expense_delete'),
    
    
    path('dashboard/restaurant-purchase-cost/list', restaurant_view.rest_purchase_cost_list, name='rest_purchase_cost_list'),
    path('dashboard/restaurant-purchase-cost/add/', restaurant_view.rest_purchase_cost_add, name='rest_purchase_cost_add'),
    path('dashboard/restaurant-purchase-cost/edit/<int:pk>/', restaurant_view.rest_purchase_cost_edit, name='rest_purchase_cost_edit'),
    path('dashboard/restaurant-purchase-cost/delete/<int:pk>/', restaurant_view.rest_purchase_cost_delete, name='rest_purchase_cost_delete'),
    
    
    
    ###  Restaurant Category ###
    #path('dashboard/restau/requisitions/ledger/history', restaurant_view.rest_project_ledger_history, name='rest_project_ledger_history'),
    
    path('dashboard/restau/requisitions/list/', restaurant_view.restau_requisition_list, name='restau_requisition_list'),
    path('dashboard/restau/requisitions/', restaurant_view.rest_requisitions_create, name='rest_requisitions_create'),
    path('requisition/restau/by-project/<int:requi_id>/', restaurant_view.restu_requisition_by_project, name='restu_requisition_by_project'),
    path('requisition/restau/requisitions/by-details/<int:project_id>/', restaurant_view.restu_requisition_by_fallback, name='restu_requisition_by_fallback'),
    path('dashboard/restau/requisitions/edit/<int:pk>/', restaurant_view.restau_requisition_edit, name='restau_requisition_edit'),
    path('dashboard/restau/requisitions/delete/<int:pk>/', restaurant_view.restau_requisition_delete, name='restau_requisition_delete'), 
    
    
	path('dashboard/restau/requisition/details/<int:pk>/', restaurant_view.requisition_details_view, name='rest_requisition_detail'),
	
	path('dashboard/restau/requisition-confirmation/', restaurant_view.restu_requisition_confirmation, name='restu_requisition_confirmation'),
	
	#path("restuarant-get-stock-qty/", restaurant_view.restuarant_get_stock_qty, name="restuarant_get_stock_qty"),
	#path('restau/requisition_update_ajax/', restaurant_view.restu_requisition_update_ajax, name='restu_requisition_update_ajax'),
	
	path('dashboard/restau/requisition-acct-confirmation/', restaurant_view.rest_requisition_acct_confirmation, name='rest_requisition_acct_confirmation'),
    #path('dashboard/restau/requisition-acct-confirmation/', restaurant_view.rest_requisition_acct_confirmation, name='rest_requisition_accounts_confirm'),
    
    # Approval History List
    path(
        'dashboard/restau/requisition-history/',
        restaurant_view.requisition_approval_history_list,
        name='requisition_approval_history_list'
    ),
    
    path('dashboard/restau/requisition-history/ledger/',  restaurant_view.requisition_jewel_ledger_list,  name='requisition_jewel_ledger_list'),
    path('dashboard/restau/restaurant-jewel-ledger/manage/', restaurant_view.rest_jewel_ledger_manage, name='rest_jewel_ledger_manage'),
    path('ajax/get-restaurant-employees/', restaurant_view.get_restaurant_employees_by_project, name='ajax_get_restaurant_employees'),
    path('dashboard/restau/restaurant-jewel-ledger/report/', restaurant_view.rest_jewel_ledger_report, name='rest_jewel_ledger_report'),
    path('dashboard/restau/restaurant-jewel-ledger/view/', restaurant_view.rest_jewel_ledger_manage_pdf, name='rest_jewel_ledger_manage_pdf'),
    
    
    # Approval History Details
    path(
        'dashboard/restau/requisition-history/details/<int:history_id>/',
        restaurant_view.requisition_approval_history_details,
        name='requisition_approval_history_details'
    ),

	path('dashboard/restau/requisition-item-summary/', restaurant_view.rest_requisition_item_summary, name='rest_requisition_item_summary'),
	path('dashboard/restau/requisition-item-approved/<int:requi_uniq_id>/', restaurant_view.restu_requisition_approved, name='restu_requisition_approved'),
	
	
	## -- Public Link ---
	path('restaurant/public-requisition/',  restaurant_view.public_rest_requisition_create, name='public_rest_requisition_create'),
	path('public/rest-requisition/', restaurant_view.public_rest_requisition_list, name='public_rest_requisition_list'),
    path('restaurant/requisition/print/', restaurant_view.print_day_wise_requisitions, name='print_day_wise_requisitions'),
    
	
    path('attendance/restau/add-holiday/', restaurant_view.rest_attendance_add_holiday, name='rest_attendance_add_holiday'),
    
    path('dashboard/restaurant-category/', restaurant_view.restaurant_category, name='restaurant_requisition_category'),
    path('dashboard/restaurant-category/add/', restaurant_view.add_restaurant_category, name='add_restaurant_category'),
    path('dashboard/restaurant-category/edit/<int:pk>/', restaurant_view.restaurant_category_edit, name='restaurant_category_edit'),
    path('dashboard/restaurant-category/delete/<int:pk>/', restaurant_view.restaurant_category_delete, name='restaurant_category_delete'),
    

    ###  Restaurant Item Name ###
    path('dashboard/restaurant-item-name/', restaurant_view.restaurant_item_name, name='restaurant_item_name'),
    path('dashboard/restaurant-item-name/add/', restaurant_view.add_restaurant_item_name, name='add_restaurant_item_name'),
    path('dashboard/restaurant-item/edit/<int:pk>/', restaurant_view.edit_restaurant_item, name='edit_restaurant_item'),
    path('dashboard/restaurant-item/delete/<int:pk>/', restaurant_view.delete_restaurant_item, name='delete_restaurant_item'),
    
    ###  Restaurant Head of Account Name ###
    path('dashboard/head-account-name/', restaurant_view.head_account_name, name='head_account_name'),
    path('dashboard/head-account-name/add/', restaurant_view.add_head_account_name, name='add_head_account_name'),
    path('dashboard/head-account/edit/<int:pk>/', restaurant_view.restaurant_headofacct_edit, name='restaurant_headofacct_edit'),
    path('dashboard/head-account/delete/<int:pk>/', restaurant_view.restaurant_headofacct_delete, name='restaurant_headofacct_delete'),


    ###  Restaurant Account Name List ###
    path('dashboard/account-name/list', restaurant_view.account_name_list, name='account_name_list'),
    path('dashboard/account-name/add/', restaurant_view.add_account_name, name='add_account_name'),
    path('dashboard/account-name/edit/<int:pk>/', restaurant_view.edit_restaurant_account, name='edit_restaurant_account'),
    path('dashboard/account-name/delete/<int:pk>/', restaurant_view.delete_restaurant_account, name='delete_restaurant_account'),


    ###  Restaurant Customer Name ###
    path('dashboard/restaurant-customer-name/', restaurant_view.restaurant_customer_name, name='restaurant_customer_name'),
    path('dashboard/restaurant-customer-name/add/', restaurant_view.add_restaurant_customer, name='add_restaurant_customer'),
    path('dashboard/restaurant-customer/edit/<int:pk>/', restaurant_view.edit_restaurant_customer, name='edit_restaurant_customer'),
    path('dashboard/restaurant-customer/delete/<int:pk>/', restaurant_view.delete_restaurant_customer, name='delete_restaurant_customer'),
    
    path('dashboard/restaurant-customer/print-auto/<int:pk>/', restaurant_view.delete_restaurant_customer, name='print_restaurant_invoice'),
    
    
    
    # Loan Payment URLs
    path(
        'attendance/public/restaurant/portal/',
        restahrm_view.public_attendance_portal,
        name='public_attendance_portal'
    ),
    path(
        'attendance/public/restaurant/emp/portal/',
        restahrm_view.public_attendance_emp_portal,
        name='public_attendance_emp_portal'
    ),
   
    path('attendance/public/restaurant/', restahrm_view.public_attendance_restaurant, name='public_attendance_restaurant'),
    path('attendance/manage-access/restaurant/', restahrm_view.manage_attendance_access_restaurant, name='manage_attendance_access_restaurant'),
    
    path("attendance/public/project/check/attendance/restcafe/", restahrm_view.public_attendance_resthrmcafe_check, name="public_attendance_resthrmcafe_check"),
    path("attendance/public/project/check/attendance/restlive/", restahrm_view.public_attendance_resthrmlive_check, name="public_attendance_resthrmlive_check"),
    
    path('dashboard/restaurant/loan/', restahrm_view.restau_loanPayment_list, name='restau_loanPayment_list'),
    path('dashboard/restaurant/loan/add/', restahrm_view.restau_loanPayment_add, name='restau_loanPayment_add'),
    path('dashboard/restaurant/loan/edit/<int:pk>/', restahrm_view.restau_loanpayment_edit, name='restau_loanpayment_edit'),
    path('dashboard/restaurant/loan/delete/<int:pk>/', restahrm_view.restau_loanpayment_delete, name='restau_loanpayment_delete'),
    
    
    # Leave URLs
    path('dashboard/restaurant/leave/', restahrm_view.restau_leavelist, name='restau_leavelist'),
    path('dashboard/restaurant/leave/rest-apply/', restahrm_view.rest_leaveapply, name='rest_leaveapply'),
    path('dashboard/restaurant/leave/edit/<int:pk>/', restahrm_view.restu_leave_edit, name='restu_leave_edit'),
    path('dashboard/restaurant/leave/delete/<int:pk>/', restahrm_view.restu_leave_delete, name='restu_leave_delete'),
    path('dashboard/restaurant/leave-summary/', restahrm_view.restu_employee_leave_summary, name='restu_employee_leave_summary'),
    path('dashboard/restaurant/approval/<int:pk>/', restahrm_view.restu_leave_approval, name='restu_leave_approval'),
    
    path('dashboard/restaurant/allocation/', restahrm_view.restu_allocation_list, name='restu_allocation_list'),
    path('dashboard/restaurant/allocation/create/', restahrm_view.restu_allocation_create, name='restu_allocation_create'),
    path('dashboard/restaurant/allocation/edit/<int:pk>/', restahrm_view.restu_allocation_edit, name='restu_allocation_edit'),
    path('dashboard/restaurant/allocation/delete/<int:pk>/', restahrm_view.restu_allocation_delete, name='restu_allocation_delete'),
    
    
    # Restua Salry URLs
    path('dashboard/restaurant/Salary/', restahrm_view.rest_salary_list, name='rest_salary_list'),
    path('dashboard/restaurant/Salary/add', restahrm_view.rest_salary_create, name='rest_salary_create'),
    path('dashboard/restaurant/Salary/edit/<int:pk>/', restahrm_view.rest_salary_edit, name='rest_salary_edit'),
    path('dashboard/restaurant/Salary/delete/<int:pk>/', restahrm_view.rest_salary_delete, name='rest_salary_delete'),
    
    # Restua Foodbill URLs
    path('dashboard/restaurant/FoodBill/', restahrm_view.rest_foodbill_list, name='rest_foodbill_list'),
    path('dashboard/restaurant/FoodBill/add', restahrm_view.rest_foodbill_create, name='rest_foodbill_create'),
    path('dashboard/restaurant/FoodBill/edit/<int:pk>/', restahrm_view.rest_foodbill_edit, name='rest_foodbill_edit'),
    path('dashboard/restaurant/FoodBill/delete/<int:pk>/', restahrm_view.rest_foodbill_delete, name='rest_foodbill_delete'),
    
    path('dashboard/contractor-payment/add/<int:id>/', accounting_views.requi_contractor_payment, name='requi_contractor_payment'),
    
    # Restua IOM URLs
    path('dashboard/restaurant/IOM/list', restahrm_view.restau_iom_list, name='restau_iom_list'),
    path('dashboard/restaurant/IOM/add', restahrm_view.restau_iom_apply, name='restau_iom_apply'),
    path('dashboard/restaurant/IOM/Edit/<int:pk>/', restahrm_view.restau_iom_edit, name='restau_iom_edit'),
    path('dashboard/restaurant/IOM/Delete/<int:pk>/', restahrm_view.restau_iom_delete, name='restau_iom_delete'),
    path('dashboard/restaurant/IOM/approval/<int:pk>/', restahrm_view.restau_iom_approval, name='restau_iom_approval'),
    path('dashboard/restaurant/IOM/summary/', restahrm_view.restau_employee_iom_summary, name='restau_employee_iom_summary'),
    
    
    ## Restuarant heque manage ---
    path('dashboard/restaccounting-capital-accounts/', restaccounting_view.rest_capital_account_list, name='rest_capital_account_list'),
    path('dashboard/restaccounting/capital-accounts/add/', restaccounting_view.rest_capital_account_add, name='rest_capital_account_add'),
    path('dashboard/restaccounting/capital-accounts/edit/<int:pk>/', restaccounting_view.rest_capital_account_edit, name='rest_capital_account_edit'),
    path('dashboard/restaccounting/capital-accounts/delete/<int:pk>/', restaccounting_view.rest_capital_account_delete, name='rest_capital_account_delete'),
    
    path('dashboard/restaccounting-main-books/list', restaccounting_view.rest_main_cheque_book_list, name='rest_main_cheque_book_list'),
    path('dashboard/restaccounting-main-books/list/<int:book_id>/cheques/', restaccounting_view.rest_main_cheque_list, name='rest_main_cheque_list'),
    path('dashboard/restaccounting-main-books/print/<int:book_id>/', restaccounting_view.rest_cheque_book_print, name='rest_cheque_book_print'),
    path('dashboard/restaccounting-main-edit-book/<int:pk>/', restaccounting_view.rest_main_edit_book, name='rest_main_edit_book'),
    path('dashboard/restaccounting-main-delete-book/<int:pk>/', restaccounting_view.rest_main_delete_book, name='rest_main_delete_book'),
    path('dashboard/restaccounting-main-edit-cheque/<int:pk>/', restaccounting_view.rest_main_edit_cheque, name='rest_main_edit_cheque'),
    path('dashboard/restaccounting-main-delete-cheque/<int:pk>/', restaccounting_view.rest_main_delete_cheque, name='rest_main_delete_cheque'),
    
    
    # Restua Cash Type URLs
    path('dashboard/restaccounting/Cash-Type/', restaccounting_view.rest_cash_type_list, name='rest_cash_type_list'),
    path('dashboard/restaccounting/Cash-Type-add/', restaccounting_view.rest_add_cash_type, name='rest_add_cash_type'),
    path('dashboard/restaccounting/Cash-Type-edit/<int:pk>/', restaccounting_view.rest_edit_cash_type, name='rest_edit_cash_type'),
    path('dashboard/restaccounting/Cash-Type-delete/<int:pk>/', restaccounting_view.rest_delete_cash_type, name='rest_delete_cash_type'),
    
    
    ## Restuarent Customer Ledger ---
    path('dashboard/restaccounting/customer-summary/list', restaccounting_view.rest_customer_summary_report, name='rest_customer_summary_report'),
    path('dashboard/restaccounting/customer-ledger-manage', restaccounting_view.rest_customer_ledger_manage, name='rest_customer_ledger_manage'),
    path('dashboard/restaccounting/customer-ledger-report', restaccounting_view.rest_customer_ledger_report, name='rest_customer_ledger_report'),
    path('dashboard/restaccounting/customer-ledger-report-pdf/print/', restaccounting_view.rest_customer_ledger_manage_pdf, name='rest_customer_ledger_manage_pdf'), 
    
    
     # Restua Sales Type URLs
    path('dashboard/restaccounting/Sales-Type/', restaccounting_view.rest_sales_type_list, name='rest_sales_type_list'),
    path('dashboard/restaccounting/Sales-Type/add', restaccounting_view.rest_add_sales_type, name='rest_add_sales_type'),
    path('dashboard/restaccounting/Sales-Type/edit/<int:pk>/', restaccounting_view.rest_edit_sales_type, name='rest_edit_sales_type'),
    path('dashboard/restaccounting/Sales-Type/Delete/<int:pk>/', restaccounting_view.rest_delete_sales_type, name='rest_delete_sales_type'),
    
    # Restua Collection Type URLs
    path('dashboard/restaccounting/Collection-add/', restaccounting_view.collection_create, name='collection_add'),
    path('dashboard/restaccounting/Collection-list/', restaccounting_view.collection_list, name='collection_list'),
    path('dashboard/restaccounting/Collection-edit/<int:pk>/', restaccounting_view.collection_edit, name='collection_edit'),
    path('dashboard/restaccounting/Collection-delete/<int:pk>/', restaccounting_view.collection_delete, name='collection_delete'),
    
    path('dashboard/restaccounting/Collection-month', restaccounting_view.month_collection_list, name='month_collection_list'),
    
    
    path('dashboard/restaccounting/Dayli-payment-add/restaurent/', restaccounting_view.restaurant_kitchen_ledger_payment, name='restaurant_kitchen_ledger_payment'),
     
    
    path('dashboard/restaccounting/Dayli-payment-add/', restaccounting_view.daily_payment_create, name='daily_payment_add'),
    path('dashboard/restaccounting/daily-payment-list/', restaccounting_view.daily_payment_list, name='daily_payment_list'),
    path('dashboard/restaccounting/daily-payment-edit/<int:pk>/', restaccounting_view.daily_payment_edit, name='daily_payment_edit'),
    path('dashboard/restaccounting/daily-payment-delete/<int:pk>/', restaccounting_view.daily_payment_delete, name='daily_payment_delete'),
     
     
    path('dashboard/restaccounting/account-head/list/', restaccounting_view.rest_head_of_account_list, name='rest_head_of_account_list'),
    path('dashboard/restaccounting/account-cradit/', restaccounting_view.rest_creditvoucher_list, name='rest_creditvoucher_list'),
    
    path('dashboard/restaccounting/account-cradit/', restaccounting_view.rest_creditvoucher_list, name='rest_creditvoucher_list'),
    path('dashboard/restaccounting/account-cradit/add', restaccounting_view.rest_add_creditvoucher, name='rest_add_creditvoucher'),
    path('dashboard/restaccounting/account-cradit/edit/<int:pk>/', restaccounting_view.rest_edit_creditvoucher, name='rest_edit_creditvoucher'),
    path('dashboard/restaccounting/account-cradit/delete/<int:pk>/', restaccounting_view.rest_delete_creditvoucher, name='rest_delete_creditvoucher'),
    path('dashboard/restaccounting/account-cradit/view/<int:pk>/', restaccounting_view.rest_credit_voucher_pdf, name='rest_credit_voucher_pdf'),
    path('dashboard/restaccounting/account-cradit/approval/<int:pk>/', restaccounting_view.rest_approve_cr_voucher, name='rest_approve_cr_voucher'),
    
    path('dashboard/restaccounting/account-allcradit/view/', restaccounting_view.rest_credit_allvoucher_approve, name='rest_credit_allvoucher_approve'),
    path('dashboard/restaccounting/account-cradit/approval/', restaccounting_view.rest_all_approve_cr_voucher, name='rest_all_approve_cr_voucher'),
    
    
    path('dashboard/restaccounting/account-head/add', restaccounting_view.rest_add_head_of_account, name='rest_add_head_of_account'),
    path('dashboard/restaccounting/account-head/edit/<int:pk>/', restaccounting_view.rest_edit_head_of_account, name='rest_edit_head_of_account'),
    path('dashboard/restaccounting/account-head/delete/<int:pk>/', restaccounting_view.rest_delete_head_of_account, name='rest_delete_head_of_account'),
    
    
    path('dashboard/restaccounting/account-debit/', restaccounting_view.rest_debitvoucher_list, name='rest_debitvoucher_list'),
    path('dashboard/restaccounting/account-debit/add', restaccounting_view.rest_add_debitvoucher, name='rest_add_debitvoucher'),
    path('dashboard/restaccounting/account-debit/edit/<int:pk>/', restaccounting_view.rest_edit_debitvoucher, name='rest_edit_debitvoucher'),
    path('dashboard/restaccounting/account-debit/delete/<int:pk>/', restaccounting_view.rest_delete_debitvoucher, name='rest_delete_debitvoucher'),
    path('dashboard/restaccounting/account-debit/view/<int:pk>/', restaccounting_view.rest_debit_voucher_pdf, name='rest_debit_voucher_pdf'),
    path('dashboard/restaccounting/account-debit/approval/<int:pk>/', restaccounting_view.rest_approve_dr_voucher, name='rest_approve_dr_voucher'),
    
    #path('dashboard/restaccounting/account-alldebit/view/', restaccounting_view.rest_debit_allvoucher_approve, name='rest_debit_allvoucher_approve'),
    #path('dashboard/restaccounting/account-debit/approval/', restaccounting_view.rest_all_approve_dr_voucher, name='rest_all_approve_dr_voucher'),
    
    
    path('dashboard/restaccounting/rest-loan-pdf/<int:pk>/', restaccounting_view.rest_loan_voucher_pdf, name='rest_loan_voucher_pdf'),
    path('dashboard/restaccounting/rest-loan-debit/edit/<int:pk>/', restaccounting_view.rest_edit_loanvoucher, name='rest_edit_loanvoucher'),
    path('dashboard/restaccounting/rest-loan-debit/delete/<int:pk>/', restaccounting_view.rest_delete_loanvoucher, name='rest_delete_loanvoucher'),
    
    
    path('dashboard/restaccounting/account-loan/', restaccounting_view.rest_loanvoucher_list, name='rest_loanvoucher_list'),
    path('dashboard/restaccounting/account-loan/add', restaccounting_view.rest_add_loanvoucher, name='rest_add_loanvoucher'),
    path('dashboard/restaccounting/account-loan/pay', restaccounting_view.rest_loanvoucher_pay_list, name='rest_loanvoucher_pay_list'),
    path('dashboard/restaccounting/account-loan/recv', restaccounting_view.rest_loanvoucher_recv_list, name='rest_loanvoucher_recv_list'),
    
    path('dashboard/restaccounting/account-transfer/', restaccounting_view.rest_transfer_list, name='rest_transfer_list'),
    path('dashboard/restaccounting/account-transfer/add', restaccounting_view.rest_transfer_add, name='rest_transfer_add'),
    path('dashboard/restaccounting/account-transfer/details/<int:pk>/', restaccounting_view.rest_transfer_detail, name='rest_transfer_detail'),
    
    path('dashboard/restaccounting/account-transfer/add', restaccounting_view.rest_add_rechvoucher, name='rest_add_rechvoucher'),
    path('dashboard/restaccounting/account-transfer/add', restaccounting_view.rest_add_rechvoucher, name='rest_add_rechvoucher'),
    
    path('dashboard/restaccounting/account-ledgermanage-list/', restaccounting_view.rest_ledger_manage_list, name='rest_ledger_manage_list'),
    
    path('dashboard/restaccounting/account-ledgermanage-list/ledger', restaccounting_view.rest_transaction_ledger_manage, name='rest_transaction_ledger_manage'),
    path('dashboard/restaccounting/account-ledgermanage-list/report', restaccounting_view.rest_transaction_ledger_report, name='rest_transaction_ledger_report'),
    path('dashboard/restaccounting/account-ledgermanage/view', restaccounting_view.rest_transaction_ledger_manage_pdf, name='rest_transaction_ledger_manage_pdf'),
    
    
     ###   Restaurant Supplier Ledger Reports module ###
    path('dashboard/restaccounting/supplier-report-manage/list', restaccounting_view.rest_supplier_reports_manage_list, name='rest_supplier_reports_manage_list'),
    path('dashboard/restaccounting/supplier-ledger-manage-sup', restaccounting_view.rest_supplier_ledger_manage, name='rest_supplier_ledger_manage'),
    path('dashboard/restaccounting/supplier-ledger-report-sup', restaccounting_view.rest_supplier_ledger_report, name='rest_supplier_ledger_report'),
    #path('dashboard/restaccounting/supplier-ledger-report-sup-pdf/print/', restaccounting_view.rest_supplier_ledger_manage_pdf, name='rest_supplier_ledger_manage_pdf'), 
    
    
    
    
    ###  Restaurant Ledger Reports module ###
    path('dashboard/restaccounting/report-manage/list', restaccounting_view.rest_reports_manage_list, name='rest_reports_manage_list'),
    path('dashboard/restaccounting/ledger-manage/', restaccounting_view.rest_ledger_manage, name='rest_ledger_manage'),
    path('dashboard/restaccounting/ledger-report/', restaccounting_view.rest_ledger_report, name='rest_ledger_report'),
    path('dashboard/restaccounting/ledger-report-sup-pdf/print/', restaccounting_view.rest_ledger_manage_pdf, name='rest_ledger_manage_pdf'), 
    
     ## Genarel Ledger Ne urls--
    path('rest-get-types-by-head/<int:head_id>/', restaccounting_view.rest_get_types_by_head, name='rest_get_types_by_head'),
    path('rest-get-projects-by-head-cash/<int:head_id>/<int:cash_type_id>/', restaccounting_view.rest_get_projects_by_head_cash, name='rest_get_projects_by_head_cash'),
    
    
    ###  Restaurant Report Name ###
    path('dashboard/restaccounting/restaurant-collection-ledger/', restaccounting_view.rest_collection_ledger, name='rest_collection_ledger'),
    path('dashboard/restaccounting/restaurant-dailypayment-ledger/', restaccounting_view.rest_dailyPayment_ledger, name='rest_dailyPayment_ledger'),
    
    path('dashboard/restaccounting/restaurant-employee-ledger/', restaccounting_view.rest_employee_summary_report, name='rest_employee_summary_report'),
    path('dashboard/restaccounting/restaurant-employee-ledger/manage', restaccounting_view.rest_employee_ledger_manage, name='rest_employee_ledger_manage'),
    path('dashboard/restaccounting/restaurant-employee-ledger/report', restaccounting_view.rest_employee_ledger_report, name='rest_employee_ledger_report'),
    path('dashboard/restaccounting/restaurant-employee-ledger/view', restaccounting_view.rest_employee_ledger_manage_pdf, name='rest_employee_ledger_manage_pdf'),
    
    path('dashboard/restaccounting/restaurant-project-ledger/', restaccounting_view.rest_project_ledger_list, name='rest_project_ledger_list'),
    path('dashboard/restaccounting/restaurant-project-ledger/manage', restaccounting_view.rest_project_ledger_manage, name='rest_project_ledger_manage'),
    path('dashboard/restaccounting/restaurant-project-ledger/report', restaccounting_view.rest_project_ledger_report, name='rest_project_ledger_report'),
    path('dashboard/restaccounting/restaurant-project-ledger/view', restaccounting_view.rest_project_ledger_manage_pdf, name='rest_project_ledger_manage_pdf'),
     
    
    path('dashboard/restaccounting/restaurant-bank-ledger/', restaccounting_view.rest_bank_ledger_manage, name='rest_bank_ledger_manage'),
    path('dashboard/restaccounting/restaurant-bank-list/', restaccounting_view.rest_bank_reports_list, name='rest_bank_reports_list'),
    path('dashboard/restaccounting/restaurant-bank-report/', restaccounting_view.rest_bank_ledger_report, name='rest_bank_ledger_report'),
    path('dashboard/restaccounting/restaurant-bank-view/', restaccounting_view.rest_bank_ledger_manage_pdf, name='rest_bank_ledger_manage_pdf'),
    
    path('dashboard/restaccounting/restaurant-transaction-ledger/', restaccounting_view.rest_transaction_reports_list, name='rest_transaction_reports_list'),
    
    
    ###  Restaurant Supplier Name ###
    path('dashboard/restaurant-supplier-name/', restaurant_view.restaurant_supplier_name, name='restaurant_supplier_name'),
    path('dashboard/restaurant-supplier-name/add/', restaurant_view.add_restaurant_supplier, name='add_restaurant_supplier'),
    path('dashboard/restaurant-supplier/edit/<int:pk>/', restaurant_view.edit_restaurant_supplier, name='edit_restaurant_supplier'),
    path('dashboard/restaurant-supplier/delete/<int:pk>/', restaurant_view.delete_restaurant_supplier, name='delete_restaurant_supplier'),
    
    
    
    ###  Restaurant Supplier Name ###
    path('dashboard/restaurant-jewel-supplier-name/', restaurant_view.restaurant_jewel_supplier_name, name='restaurant_jewel_supplier_name'),
    path('dashboard/restaurant-jewel-supplier-name/add/', restaurant_view.add_restaurant_jewel_supplier, name='add_restaurant_jewel_supplier'),
    path('dashboard/restaurant-jewel-supplier/edit/<int:pk>/', restaurant_view.edit_restaurant_jewel_supplier, name='edit_restaurant_jewel_supplier'),
    path('dashboard/restaurant-jewel-supplier/delete/<int:pk>/', restaurant_view.delete_restaurant_jewel_supplier, name='delete_restaurant_jewel_supplier'),
    
    

    ###  Restaurant Item Amount List ###    
    path("dashboard/restaurant-item-amount/list", restaurant_view.restaurant_item_amount_list, name="restaurant_item_amount_list"),
    path('dashboard/restaurant-item-amount/get-item-data/', restaurant_view.get_item_amount_data, name='get_item_amount_data'),
    path("dashboard/restaurant-item-amount/delete/", restaurant_view.delete_items, name="delete_items"),
    path("dashboard/restaurant-item-amount/add", restaurant_view.restaurant_item_amount_add, name="restaurant_item_amount_add"),
    path("dashboard/restaurant-item-amount/load-items/", restaurant_view.load_items, name="load_items"), 

    path("dashboard/restaurant-item-sales/list", restaurant_view.restaurant_sales_list, name="restaurant_sales_list"),
    path('dashboard/restaurant/invoice/<int:sale_id>/', restaurant_view.restaurant_invoice_view, name='restaurant_invoice_view'),
    path('restaurant-sales/challan/<int:sale_id>/', restaurant_view.restaurant_sales_challan, name='restaurant_sales_challan'),
    
    path('restaurant/damage/record/', restaurant_view.record_damage_food, name='record_damage_food'),
    
    path('restaurant/shift/dashboard/', restaurant_view.shift_dashboard, name='shift_dashboard'),
    path('restaurant/shift/start/', restaurant_view.start_work, name='start_work'),
    path('restaurant/shift/opening-report/<int:shift_id>/', restaurant_view.opening_stock_report, name='opening_stock_report'),
    path('restaurant/shift/stop/', restaurant_view.stop_work, name='stop_work'),
    path('restaurant/shift/request-stock/', restaurant_view.request_stock_increase, name='request_stock_increase'),
    path('restaurant/shift/approve-stock/<int:req_id>/', restaurant_view.approve_requisition, name='approve_requisition'),
    path('restaurant/shift/damage-food/add/', restaurant_view.add_damage_food, name='add_damage_food'),
    path('restaurant/shift/report/<int:shift_id>/', restaurant_view.shift_report, name='shift_report'),
    

    
    ###  Restaurant Sales Report ###   
    path('dashboard/restaurant/sales/reports/', restaurant_view.restaurant_sales_report, name='restaurant_sales_report'),
    path('dashboard/restaurant-sales/edit/<int:pk>/', restaurant_view.edit_restaurant_sales, name='edit_restaurant_sales'),
    path('dashboard/restaurant-sales/delete/<int:pk>/', restaurant_view.delete_restaurant_sales, name='delete_restaurant_sales'),
    path('dashboard/restaurant/sales/<int:sale_id>/', restaurant_view.restaurant_sales_view, name='restaurant_sales_view'),
    path('dashboard/daily-salary-history/', restaurant_view.daily_salary_history, name='daily_salary_history'),
    
    
    ## - Restaurant HRM ----
    path('dashboard/restaurant/employee/details', restahrm_view.restaurant_employee_details, name='restaurant_employee_details'),
    path('dashboard/restaurant/employee/project/details/', restahrm_view.restaurant_employee_project_details, name='restaurant_employee_project_details'),
    
    ##RDA Employee -- 
    path('dashboard/restaurant/employees/', restahrm_view.restaurant_employee_list, name='restaurant_employee_list'),
    path('dashboard/restaurant/employees/toggle/<int:pk>/', restahrm_view.restaurant_employee_toggle_status, name='restaurant_employee_toggle_status'),
    path('dashboard/restaurant/employees/add/', restahrm_view.restaurant_employee_add, name='restaurant_employee_add'),
    path('dashboard/restaurant/employees/<int:pk>/edit/', restahrm_view.restaurant_employee_edit, name='restaurant_employee_edit'),
    path('dashboard/restaurant/employees/delete/<int:pk>/', restahrm_view.restaurant_employee_delete, name='restaurant_employee_delete'),
    
    path('dashboard/restaurant/monthly-salary-report/', restahrm_view.restaurant_monthly_salary_generate, name='restaurant_monthly_salary_generate'),
    #path('dashboard/restaurant/monthly-salary-report/check/', restahrm_view.monthly_salary_check, name='monthly_salary_check'),
    path("approve/restaurant/<int:project_id>/<str:month_name>/", restahrm_view.restaurant_approve_salary_generate, name="restaurant_approve_salary_generate"),
    
    # # Attendance URLs
    path('dashboard/restaurant/attendance/', restahrm_view.restaurant_attendance_list, name='restaurant_attendance_list'),
    path('dashboard/restaurant/attendance/add/', restahrm_view.restaurant_attendance_create, name='restaurant_attendance_add'),
    path('dashboard/restaurant/attendance/edit/<int:pk>/', restahrm_view.restaurant_attendance_edit, name='restaurant_attendance_edit'),
    path('dashboard/restaurant/attendance/delete/<int:pk>/', restahrm_view.restaurant_attendance_delete, name='restaurant_attendance_delete'),
    path('dashboard/restaurant/attendance-summary/', restahrm_view.restaurant_employee_attendance_summary, name='restaurant_employee_attendance_summary'),
    
    
    ## Shift schedule --
    path("dashboard/shift/", restahrm_view.shift_list, name="shift_list"),
    path("dashboard/shift/add/", restahrm_view.shift_add, name="shift_add"),
    path("dashboard/shift/edit/<int:pk>/", restahrm_view.shift_edit, name="shift_edit"),
    path("dashboard/shift/delete/<int:pk>/", restahrm_view.shift_delete, name="shift_delete"),
    
    
    
    path('dashboard/restaurant/payroll/', restahrm_view.restaurant_payroll_list, name='restaurant_payroll_list'),
    path('dashboard/restaurant/payslip/print', restahrm_view.restaurant_payslip_print, name='restaurant_payslip_print'),
    path('dashboard/restaurant/payroll/print', restahrm_view.restaurant_payroll_print, name='restaurant_payroll_print'),
    
    path('dashboard/restaurant/attendance/<int:pk>/checkout-update/', restahrm_view.RestaurantAttendanceCheckoutUpdateView, name='restaurant_attendance_checkout_update'),
    
    path('dashboard/restaurant/payroll/print/manual', restahrm_view.restaurant_payroll_print_manual, name='restaurant_payroll_print_manual'),
    
    # # Advance Payment URLs
    path('dashboard/restaurant/advance/list', restahrm_view.restaurant_advance_list, name='restaurant_advance_list'),
    path('dashboard/restaurant/advance/add/', restahrm_view.restaurant_advance_create, name='restaurant_advance_add'),
    path('dashboard/restaurant/advance/edit/<int:pk>/', restahrm_view.restuarant_advance_edit, name='restuarant_advance_edit'),
    path('dashboard/restaurant/advance/delete/<int:pk>/', restahrm_view.restuarant_advance_delete, name='restuarant_advance_delete'),
    path('dashboard/restaurant/advance/view/<int:pk>/', restahrm_view.restaurant_advance_pdf, name='restaurant_advance_pdf'),
    
    
    # Allowances Payment URLs
    path('dashboard/restaurant/allowances/', restahrm_view.restau_allowances_list, name='restau_allowances_list'),
    path('dashboard/restaurant/allowances/add/', restahrm_view.restau_allowances_create, name='restau_allowances_create'),
    path('dashboard/restaurant/allowances/edit/<int:pk>/', restahrm_view.restau_allowances_edit, name='restau_allowances_edit'),
    path('dashboard/restaurant/allowances/delete/<int:pk>/', restahrm_view.restau_allowances_delete, name='restau_allowances_delete'),
    

    ] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)



## for app api 404 error manage ----
from django.http import JsonResponse

def custom_page_not_found(request, exception=None):
    return JsonResponse({
        "404": "Error",
        "code": "not_found",
        "messages": [
            {"message": f"The requested URL {request.path} was not found"}
        ]
    }, status=404)

def custom_server_error(request):
    return JsonResponse({
        "404": "Error",
        "code": "server_error",
        "messages": [
            {"message": "An internal server error occurred"}
        ]
    }, status=500)

handler404 = custom_page_not_found
handler500 = custom_server_error
