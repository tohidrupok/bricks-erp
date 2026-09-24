from django.urls import path
from . import views

app_name = 'office_inventory'

urlpatterns = [
    path('', views.dashboard, name='dashboard'),

    path('items/', views.item_list, name='item_list'),
    path('items/add/', views.item_create, name='item_create'),
    path('items/<int:pk>/edit/', views.item_update, name='item_update'),

    path('departments/', views.department_list, name='department_list'),
    path('departments/add/', views.department_create, name='department_create'),
    path('departments/<int:pk>/', views.department_detail, name='department_detail'),
    path('departments/<int:pk>/edit/', views.department_update, name='department_update'),
    path('departments/<int:pk>/delete/', views.department_delete, name='department_delete'),
    path('ajax/load-employees/', views.load_employees, name='ajax_load_employees'),
    
    path('locations/', views.location_list, name='location_list'),
    path('locations/add/', views.location_create, name='location_create'),
    path('locations/<int:pk>/', views.location_detail, name='location_detail'),
    path('locations/<int:pk>/edit/', views.location_update, name='location_update'),
    path('locations/<int:pk>/delete/', views.location_delete, name='location_delete'),

    path('requisitions/', views.requisition_list, name='requisition_list'),
    path('requisitions/<int:pk>/edit/', views.requisition_edit, name='requisition_edit'),
    path('requisitions/<int:pk>/delete/', views.requisition_delete, name='requisition_delete'),
    path('requisitions/new/', views.requisition_create, name='requisition_create'),
    path('requisitions/<int:pk>/', views.requisition_detail, name='requisition_detail'),
    path('requisitions/<int:pk>/dept-approve/', views.requisition_dept_approve, name='requisition_dept_approve'),
    path('requisitions/<int:pk>/admin-approve/', views.requisition_admin_approve, name='requisition_admin_approve'),
    path('requisitions/<int:pk>/issue/', views.requisition_issue, name='requisition_issue'),

    path('purchases/', views.purchase_list, name='purchase_list'),
    path('purchases/new/', views.purchase_create, name='purchase_create'),
    path('purchases/<int:pk>/receive/', views.purchase_receive, name='purchase_receive'),
    path('purchases/<int:pk>/cancel/', views.purchase_cancel, name='purchase_cancel'),

    # Purchase Department panel - approve admin-approved requisitions (locked item/qty)
    path('purchases/queue/', views.purchase_queue, name='purchase_queue'),
    path('purchases/queue/<int:pk>/approve/', views.purchase_approve_requisition, name='purchase_approve_requisition'),

    path('assignments/', views.assignment_list, name='assignment_list'),
    path('assignments/new/', views.assignment_create, name='assignment_create'),
    path('assignments/<int:pk>/edit/', views.assignment_update, name='assignment_update'),
    path('assignments/<int:pk>/delete/', views.assignment_delete, name='assignment_delete'),
    path('assignments/<int:pk>/return/', views.assignment_return, name='assignment_return'),

    # Assignment Types - dynamic "who/what can an item be assigned to"
    path('assignment-types/', views.assignment_type_list, name='assignment_type_list'),
    path('assignment-types/add/', views.assignment_type_create, name='assignment_type_create'),
    path('assignment-types/<int:pk>/edit/', views.assignment_type_update, name='assignment_type_update'),
    path('assignment-types/<int:pk>/delete/', views.assignment_type_delete, name='assignment_type_delete'),
    path('assignment-types/<int:pk>/profile/', views.assignment_type_profile, name='assignment_type_profile'),

    # Employee-wise asset profile
    path('employees/', views.employee_profile_list, name='employee_profile_list'),
    path('employees/<int:pk>/profile/', views.employee_asset_profile, name='employee_asset_profile'),
    path('my-assignments/', views.my_assignments, name='my_assignments'),
    
    path('categories/', views.category_list, name='category_list'),
    path('categories/add/', views.category_create, name='category_create'),
    path('categories/<int:pk>/', views.category_detail, name='category_detail'),
    path('categories/<int:pk>/edit/', views.category_update, name='category_update'),
    path('categories/<int:pk>/delete/', views.category_delete, name='category_delete'),

    # Damage tracking
    path('damage/', views.damage_list, name='damage_list'),
    path('damage/report/', views.damage_create, name='damage_create'),
    path('damage/<int:pk>/status/', views.damage_set_status, name='damage_set_status'),
    path('damage/<int:pk>/delete/', views.damage_delete, name='damage_delete'),

    # Damage - dynamic responsible types
    path('damage/types/', views.damage_type_list, name='damage_type_list'),
    path('damage/types/add/', views.damage_type_create, name='damage_type_create'),
    path('damage/types/<int:pk>/edit/', views.damage_type_update, name='damage_type_update'),
    path('damage/types/<int:pk>/delete/', views.damage_type_delete, name='damage_type_delete'),

    # Damage - dynamic reasons
    path('damage/reasons/', views.damage_reason_list, name='damage_reason_list'),
    path('damage/reasons/add/', views.damage_reason_create, name='damage_reason_create'),
    path('damage/reasons/<int:pk>/edit/', views.damage_reason_update, name='damage_reason_update'),
    path('damage/reasons/<int:pk>/delete/', views.damage_reason_delete, name='damage_reason_delete'),

    # Reports hub + Excel/PDF export
    path('reports/', views.reports_home, name='reports_home'),
    path('reports/items/excel/', views.items_report_excel, name='items_report_excel'),
    path('reports/items/pdf/', views.items_report_pdf, name='items_report_pdf'),
    path('reports/requisitions/excel/', views.requisitions_report_excel, name='requisitions_report_excel'),
    path('reports/requisitions/pdf/', views.requisitions_report_pdf, name='requisitions_report_pdf'),
    path('reports/purchases/excel/', views.purchases_report_excel, name='purchases_report_excel'),
    path('reports/purchases/pdf/', views.purchases_report_pdf, name='purchases_report_pdf'),
    path('reports/assignments/excel/', views.assignments_report_excel, name='assignments_report_excel'),
    path('reports/assignments/pdf/', views.assignments_report_pdf, name='assignments_report_pdf'),
    path('reports/damage/excel/', views.damage_report_excel, name='damage_report_excel'),
    path('reports/damage/pdf/', views.damage_report_pdf, name='damage_report_pdf'),
]
