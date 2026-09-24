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

urlpatterns = [
    path('', home, name='home'), 
    path('login/', login, name='login'), 
    path('register/', register, name='register'),  
    path('dashboard/', dashboard, name='dashboard'), 
    path('logout/', logout, name='logout'),
    path('admin/', admin.site.urls),

    # PropertyOwner URLs ----
    path('dashboard/property_owner/', views.property_owner_list, name='property_owner_list'),
    path('dashboard/property_owner/add/', views.add_property_owner, name='add_property_owner'),
    path('dashboard/property_owner/<int:id>/detail/', views.property_owner_detail, name='property_owner_detail'),
    path('dashboard/property_owner/<int:id>/', views.edit_property_owner, name='edit_property_owner'),
    path('dashboard/property_owner/delete/<int:id>/', views.delete_property_owner, name='delete_property_owner'),

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
    path('dashboard/land-purchase/', views.land_list, name='land_list'),
    path('dashboard/land-purchase/add/', views.land_add, name='land_add'),
    path('dashboard/land-purchase/edit/<int:pk>/', views.land_edit, name='land_edit'),
    path('dashboard/land-purchase/delete/<int:pk>/', views.land_delete, name='land_delete'),
    path('dashboard/land-purchase/detail/<int:pk>/', views.land_detail, name='land_detail'),


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

    path('dashboard/rename-folder/<int:folder_id>/', documents_views.rename_folder, name='rename_folder'),
    path('dashboard/delete-folder/<int:folder_id>/', documents_views.delete_folder, name='delete_folder'),
    path('dashboard/delete-file/<int:file_id>/', documents_views.delete_file, name='delete_file'),

    # Project Location URLs ---
    path('dashboard/locations/', projects_views.project_location_list, name='project_location_list'),
    path('dashboard/locations/add/', projects_views.project_location_add, name='project_location_add'),
    path('dashboard/locations/edit/<int:pk>/', projects_views.project_location_edit, name='project_location_edit'),
    path('dashboard/locations/delete/<int:pk>/', projects_views.project_location_delete, name='project_location_delete'),

    ## Project First Level --
    path('dashboard/boq/', projects_views.boq_list, name='boq_list'),
    path('dashboard/boq-list/<int:project_id>/', projects_views.boq_list_details, name='boq_list_details'),
    #path('dashboard/boq-list/<str:project_name>/', projects_views.boq_list_details, name='boq_list_details'),
    path('dashboard/boq/add/', projects_views.boq_mate_create, name='boq_mate_create'), 
    #path('dashboard/boq/view/<int:pk>/', projects_views.boq_view, name='boq_view'),
    path('dashboard/boq/edit/<int:pk>/', projects_views.boq_edit, name='boq_edit'),  
    path('dashboard/boq/delete/<int:pk>/', projects_views.boq_delete, name='boq_delete'),
    path('dashboard/project_boq_details/', projects_views.project_boq_details, name='project_boq_details'),
    path('dashboard/boq/<int:project_id>/pdf/', projects_views.boq_pdf_view, name='boq_pdf'),
    path('dashboard/boq/category-pdf/', projects_views.boq_category_pdf, name='boq_category_pdf'),

    path('dashboard/boq/revise/<int:pk>/<int:project_id>/', projects_views.revise_boq, name='boq_revise'),
    path('dashboard/revised-item-entry/', projects_views.revised_item_entry, name='revised_item_entry'),
    
    
    #BOQ- type create
    path('dashboard/boqtype/add/', projects_views.create_boq_type, name='create_boq_type'),
    path('dashboard/boqtype/edit/<int:pk>/', projects_views.boq_type_edit, name='boq_type_edit'),
    path('dashboard/boqtype/delete/<int:pk>/', projects_views.boq_type_delete, name='boq_type_delete'),
    path('dashboard/boqtype/list/', projects_views.boq_type_list, name='boq_type_list'),



    path('dashboard/create-type/', projects_views.add_boq_type_only, name='add_boq_type_only'),
    path('dashboard/create/', projects_views.create_boq_category, name='create_boq_category'),
    path('dashboard/list/', projects_views.boq_category_list, name='boq_category_list'),
    path('dashboard/boq-category/edit/<int:id>/', projects_views.edit_boq_category, name='boq_category_edit'),
    path('dashboard/boq-category/delete/<int:id>/', projects_views.delete_boq_category, name='boq_category_delete'),

    path('dashboard/first-level/', projects_views.first_level_list, name='first_level_list'),
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

    ###   CRM Module ###
    path('dashboard/customers/', crm_views.customer_list, name='customer_list'),
    path('dashboard/customers/add/', crm_views.customer_add, name='customer_add'),
    path('dashboard/customers/edit/<int:pk>/', crm_views.customer_edit, name='customer_edit'),
    path('dashboard/customers/details/<int:pk>/', crm_views.customer_details, name='customer_details'),
    path('dashboard/customers/delete/<int:pk>/', crm_views.customer_delete, name='customer_delete'),

    path('dashboard/customer_leads/', crm_views.customer_lead_list, name='customer_lead_list'),
    path('dashboard/customer_leads/add/', crm_views.customer_lead_add, name='customer_lead_add'),
    path('dashboard/customer_leads/edit/<int:pk>/', crm_views.customer_lead_edit, name='customer_lead_edit'),
    path('dashboard/customer_leads/delete/<int:pk>/', crm_views.customer_lead_delete, name='customer_lead_delete'),
    path('dashboard/customer-leads/<int:pk>/', crm_views.customer_lead_detail, name='customer_lead_detail'),
    
    path('dashboard/leads-followup/list/', crm_views.lead_followup_list, name='lead_followup_list'),
    path('dashboard/leads/<int:lead_id>/toggle-status/', crm_views.toggle_lead_status, name='toggle_lead_status'),
    path('dashboard/leads-followup/<int:lead_id>/view/', crm_views.customer_lead_followup, name='customer_lead_followup'),


    ###   Products Module ###
    path('dashboard/products/', products_view.product_list, name='product_list'),
    path('dashboard/products/add/', products_view.add_product, name='add_product'),

    ###   Accounting Module ###
    path('dashboard/cash-types/', accounting_views.cash_type_list, name='cash_type_list'),
    path('dashboard/cash-types/add/', accounting_views.add_cash_type, name='add_cash_type'),
    path('dashboard/cash-types/edit/<int:pk>/', accounting_views.edit_cash_type, name='edit_cash_type'),
    path('dashboard/cash-types/delete/<int:pk>/', accounting_views.delete_cash_type, name='delete_cash_type'),
    
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
    
    

    ###   open balance voucher ###
    path('dashboard/openbalancevouchers/', accounting_views.openbalance_voucher_list, name='openbalance_voucher_list'),
    path('dashboard/openbalancevouchers/add/', accounting_views.add_openbalance_voucher, name='add_openbalance_voucher'),
    path('dashboard/openbalancevouchers/edit/<int:pk>/', accounting_views.edit_openbalance_voucher, name='edit_openbalance_voucher'),
    path('dashboard/openbalancevouchers/delete/<int:pk>/', accounting_views.delete_openbalance_voucher, name='delete_openbalance_voucher'),
    path('dashboard/open-balance-voucher/<int:pk>/pdf/', accounting_views.openbalance_voucher_pdf, name='openbalance_voucher_pdf'),
    

    ###  Expense Head ###
    path('dashboard/head-of-expense/', purchase_view.expense_head_list, name='expense_head_list'),
    path('dashboard/head-of-expense/add/', purchase_view.add_head_of_expense, name='add_head_of_expense'),
    path('dashboard/head-of-expense/edit/<int:pk>/', purchase_view.edit_head_of_expense, name='edit_head_of_expense'),
    path('dashboard/head-of-expense/delete/<int:pk>/', purchase_view.delete_head_of_expense, name='delete_head_of_expense'),
    
    ###  Expense list ###    
    path('dashboard/expense/list', purchase_view.expense_list, name='expense_list'),
    path('dashboard/expense/add/', purchase_view.expense_add, name='expense_add'),
    path('dashboard/expense/edit/<int:pk>/', purchase_view.expense_edit, name='expense_edit'),
    path('dashboard/expense/delete/<int:pk>/', purchase_view.expense_delete, name='expense_delete'),
    path('dashboard/expense/Details/<int:pk>/', purchase_view.expense_voucher_pdf, name='expense_voucher_pdf'), 
    path('dashboard/expense-confirmation/', purchase_view.expense_confirmation, name='expense_confirmation'),
    path('dashboard/expense-item-summary/', purchase_view.expense_item_summary, name='expense_item_summary'),
    path('dashboard/expense-admin-confirmation/<int:pk>/', purchase_view.expense_admin_confirm, name='expense_admin_confirm'),

    ###  HRM Module ### 
    path('dashboard/employee/list', hrm_view.employee_list, name='employee_list'),
    path('dashboard/employee/add/', hrm_view.employee_add, name='employee_add'),
    path('dashboard/employee/edit/<int:pk>/', hrm_view.employee_edit, name='employee_edit'),
    path('dashboard/employee-user/edit/<int:pk>/', hrm_view.employee_edit_user, name='employee_edit_user'),
    path('dashboard/employee/delete/<int:pk>/', hrm_view.employee_delete, name='employee_delete'),
    path('dashboard/employee/details/<int:pk>/', hrm_view.employee_detail, name='employee_detail'),

    path('dashboard/employee-new/add/', hrm_view.add_employee, name='add_employee'),

    # Attendance URLs
    path('dashboard/attendance/', hrm_view.attendance_list, name='attendance_list'),
    path('dashboard/attendance/add/', hrm_view.attendance_create, name='attendance_add'),
    path('dashboard/attendance/edit/<int:pk>/', hrm_view.attendance_edit, name='attendance_edit'),
    path('dashboard/attendance/delete/<int:pk>/', hrm_view.attendance_delete, name='attendance_delete'),
    path('dashboard/attendance-summary/', hrm_view.employee_attendance_summary, name='employee_attendance_summary'),
    
    path('dashboard/attendance/upload/', hrm_view.attendance_upload_csv, name='attendance_upload_csv'),


    # Payroll URLs
    path('dashboard/payroll/', hrm_view.payroll_list, name='payroll_list'),
    path('dashboard/payroll/print/', hrm_view.payroll_print, name='payroll_print'),

    # Payslip URLs
    path('dashboard/payslip/print/', hrm_view.payslip_print, name='payslip_print'),

    # Advance Payment URLs
    path('dashboard/advance/', hrm_view.advance_list, name='advance_list'),
    path('dashboard/advance/add/', hrm_view.advance_create, name='advance_add'),
    path('dashboard/advance/edit/<int:pk>/', hrm_view.advance_edit, name='advance_edit'),
    path('dashboard/advance/delete/<int:pk>/', hrm_view.advance_delete, name='advance_delete'),
    
    
    # Allowances Payment URLs
    path('dashboard/allowances/', hrm_view.allowances_list, name='allowances_list'),
    path('dashboard/allowances/add/', hrm_view.allowances_create, name='allowances_create'),
    path('dashboard/allowances/edit/<int:pk>/', hrm_view.allowances_edit, name='allowances_edit'),
    path('dashboard/allowances/delete/<int:pk>/', hrm_view.allowances_delete, name='allowances_delete'),

    
    
    # Leave URLs
    path('dashboard/leave/', hrm_view.leave_list, name='leave_list'),
    path('dashboard/leave/apply/', hrm_view.leave_apply, name='leave_apply'),
    path('dashboard/leave/edit/<int:pk>/', hrm_view.leave_edit, name='leave_edit'),
    path('dashboard/leave/delete/<int:pk>/', hrm_view.leave_delete, name='leave_delete'),
    path('dashboard/leave-summary/', hrm_view.employee_leave_summary, name='employee_leave_summary'),


    ###  Requisitions App Module ###
    path('dashboard/requisitions/', purchase_view.requisitions_create, name='requisitions_create'),
    path('dashboard/requisitions/list/', purchase_view.requisition_list, name='requisition_list'),
    path('dashboard/requisitions/project/<int:project_id>/', purchase_view.requisition_by_project, name='requisition_by_project'),
    path('dashboard/requisitions/edit/<int:pk>/', purchase_view.requisition_edit, name='requisition_edit'),
    path('dashboard/requisitions/delete/<int:pk>/', purchase_view.requisition_delete, name='requisition_delete'), 
    
    path('dashboard/project-boq-requisition-summary/', purchase_view.project_boq_requisition_summary, name='project_boq_requisition_summary'),

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
    
     ###  Requisition Comparative ###
    path('dashboard/requisition-comparative/', purchase_view.requisition_comparative_list, name='requisition_comparative_list'),
    path('dashboard/requisition-comparative/add/', purchase_view.add_requisition_comparative, name='add_requisition_comparative'),
    path('dashboard/requisition-comparative-approval/', purchase_view.requis_comparative_approval, name='requis_comparative_approval'),
    path('dashboard/requisitions-comparative/edit/<int:pk>/', purchase_view.requisition_comparative_edit, name='requisition_comparative_edit'),
    path('dashboard/requisitions-comparative/delete/<int:pk>/', purchase_view.requisition_comparative_delete, name='requisition_comparative_delete'), 
    path('dashboard/requisition-comparative-admin-confirmation/<int:pk>/', purchase_view.requisition_comparative_admin_confirm, name='requisition_comparative_admin_confirm'),
    
    path('dashboard/requisition-comparative-print/', purchase_view.requisition_comparative_print, name='requisition_comparative_print'),
    
    path('dashboard/requisition-invoice/list/', purchase_view.requisition_invoice_list, name='requisition_invoice_list'),
    path('dashboard/requisition-invoice-details/<int:pk>/', purchase_view.requisition_invoice_details, name='requisition_invoice_details'),
    
    
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


    # ... other urls
    

    ###  Purchase Module ###
    path('dashboard/requisition-approv-list/list/', purchase_view.requisition_approv_list, name='requisition_approv_list'),
    path('dashboard/purchase/list/', purchase_view.purchase_list, name='purchase_list'),
    path('dashboard/purchase-cash-details/<int:pk>/', purchase_view.purchase_cash_details, name='purchase_cash_details'),
    path('dashboard/purchase-order/list/', purchase_view.purchase_order_list, name='purchase_order_list'),
    path('dashboard/purchase-orderss-details/<int:pk>/', purchase_view.purchase_order_details, name='purchase_order_details'),
    
    path('dashboard/purchase-invoice/list/', purchase_view.purchase_invoice_list, name='purchase_invoice_list'),
    path('dashboard/purchase-invoice-details/<int:pk>/', purchase_view.purchase_invoice_details, name='purchase_invoice_details'),

    path('dashboard/update-files/<int:purch_id>/', purchase_view.update_purch_file, name='update_purch_file'),

    path('dashboard/requisition-confirmation/', purchase_view.requisition_confirmation, name='requisition_confirmation'),
    path('dashboard/requisition-details/<int:pk>/', purchase_view.requisition_detail, name='requisition_detail'),

    path('dashboard/requisition-item-summary/', purchase_view.requisition_item_summary, name='requisition_item_summary'),
    
    path('dashboard/return-purchase/list/', purchase_view.return_purchase_list, name='return_purchase_list'),
    path('dashboard/approve-return-purchase/<int:pk>/', purchase_view.approve_return_voucher, name='approve_return_voucher'),
    path('dashboard/return-purchase/item/', purchase_view.return_purchase_item, name='return_purchase_item'),
    
    
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
    path('dashboard/inventory-use/create/', inventories_view.inventory_use_create, name='inventory_use_create'),
    path('dashboard/inventory-use/list/', inventories_view.inventory_use_list, name='inventory_use_list'),
    path('dashboard/inventory-use-item-summary/', inventories_view.use_item_summary, name='use_item_summary'),

    
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
    path('dashboard/transaction-report', accounting_views.transaction_ledger_report, name='transaction_ledger_report'),
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
    path('dashboard/supplier-ledger-manage', accounting_views.supplier_ledger_manage, name='supplier_ledger_manage'),
    path('dashboard/supplier-ledger-report', accounting_views.supplier_ledger_report, name='supplier_ledger_report'),
    path('dashboard/supplier-ledger-report-pdf/print/', accounting_views.supplier_ledger_manage_pdf, name='supplier_ledger_manage_pdf'),
    
    path('dashboard/return-items/', purchase_view.return_item_list, name='return_item_list'),
    
    path('dashboard/supplier-summary/', accounting_views.supplier_summary_report, name='supplier_summary_report'),
    
    path('dashboard/purchase-summary/', accounting_views.purchase_summary_report, name='purchase_summary_report'),
    path('dashboard/purchase-ledger-manage', accounting_views.purchase_ledger_manage, name='purchase_ledger_manage'),
    path('dashboard/purchase-ledger-report/', accounting_views.purchase_ledger_report, name='purchase_ledger_report'),
    path('dashboard/purchase-ledger-report-pdf/print/', accounting_views.purchase_ledger_manage_pdf, name='purchase_ledger_manage_pdf'), 
    
     ## Genarel Ledger Ne urls--
    path('get-types-by-head/<int:head_id>/', accounting_views.get_types_by_head, name='get_types_by_head'),
    path('get-projects-by-head-cash/<int:head_id>/<int:cash_type_id>/', accounting_views.get_projects_by_head_cash, name='get_projects_by_head_cash'),


    ###  Sales List ###
    path('dashboard/sales/list', sales_view.sales_list, name='sales_list'),
    path('dashboard/sales/add/', sales_view.sales_add, name='sales_add'),
    path('dashboard/sales/edit/<int:pk>/', sales_view.sales_edit, name='sales_edit'),
    path('dashboard/sales/delete/<int:pk>/', sales_view.sales_delete, name='sales_delete'),

    ###  Others Account - Under Head of account List ###
    path('dashboard/capital-accounts/', accounting_views.capital_account_list, name='capital_account_list'),
    path('dashboard/capital-accounts/add/', accounting_views.capital_account_create, name='capital_account_add'),
    path('dashboard/capital-accounts/edit/<int:pk>/', accounting_views.capital_account_edit, name='capital_account_edit'),
    path('dashboard/capital-accounts/delete/<int:pk>/', accounting_views.capital_account_delete, name='capital_account_delete'),
    
    path('dashboard/deleted-records/', inventories_view.deleted_records_view, name='deleted_records'),
    path('dashboard/deleted-records/undo/<int:pk>/', inventories_view.undo_deleted_record, name='undo_deleted_record'),


    ] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
