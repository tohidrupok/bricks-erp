from django.urls import path
from . import views

app_name = 'tracker'

urlpatterns = [
    # Land Record
    path('', views.land_list, name='list'),
    path('create/', views.land_create, name='create'),
    path('<int:pk>/', views.land_detail, name='detail'),
    path('<int:pk>/edit/', views.land_update, name='update'),
    path('<int:pk>/delete/', views.land_delete, name='delete'),
    
    path('<int:pk>/pdf/view/',              views.land_pdf_view,     name='pdf_view'),
    path('<int:pk>/pdf/download/',          views.land_pdf_download, name='pdf_download'),
    
    # Owner nodes
    path('<int:land_pk>/owner/add/', views.owner_add, name='owner_add'),
    path('<int:land_pk>/owner/<int:owner_pk>/edit/', views.owner_update, name='owner_update'),
    path('<int:land_pk>/owner/<int:owner_pk>/delete/', views.owner_delete, name='owner_delete'),

    # AJAX
    path('<int:land_pk>/tree.json', views.tree_json, name='tree_json'),
]
