# Updated imports inside urls.py (referencing both files)
from django.urls import path
from . import views, crud_views

urlpatterns = [
    # Core Main POS Views
    path('', views.pos_terminal, name='pos_terminal'),
    path('dashboard/pos/', views.dashboard, name='dashboard_pos'),  # Mapped to your existing dashboard view
    path('order-history/', views.order_history, name='order_history'),
    path('stock-boq/', views.stock_boq_view, name='stock_boq'),
    path('work-period/toggle/', views.toggle_work_period, name='toggle_work_period'),

    # BOQ CRUD Endpoints
    path('boq/create/', crud_views.create_boq, name='create_boq'),
    path('boq/approve/<int:boq_id>/', views.approve_boq, name='approve_boq'),
    path('boq/edit/<int:pk>/', crud_views.edit_boq, name='edit_boq'),
    path('boq/delete/<int:pk>/', crud_views.delete_boq, name='delete_boq'),

    # Requisition CRUD Endpoints
    path('requisition/create/', views.create_requisition, name='create_requisition'),
    path('requisition/approve/<int:req_id>/', views.approve_requisition, name='approve_requisition'),
    path('requisition/delete/<int:pk>/', crud_views.delete_requisition, name='delete_requisition'),

    # Purchase Order CRUD Endpoints
    path('purchase-order/create/', views.create_purchase_order, name='create_purchase_order'),
    path('purchase-order/approve/<int:po_id>/', views.approve_purchase_order, name='approve_purchase_order'),
    path('purchase-order/delete/<int:pk>/', crud_views.delete_purchase_order, name='delete_purchase_order'),

    # Customer & Table CRUD Endpoints
    path('customer/create/', crud_views.create_customer, name='create_customer'),
    path('customer/edit/<int:pk>/', crud_views.edit_customer, name='edit_customer'),
    path('customer/delete/<int:pk>/', crud_views.delete_customer, name='delete_customer'),
    path('table/create/', crud_views.create_table, name='create_table'),
    path('table/delete/<int:pk>/', crud_views.delete_table, name='delete_table'),

    # Order Actions & Taka Return
    path('order/return/', views.process_taka_return, name='process_taka_return'),
    path('order/delete/<int:pk>/', crud_views.delete_order, name='delete_order'),
]