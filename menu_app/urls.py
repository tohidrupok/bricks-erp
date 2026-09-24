from django.urls import path

from . import views

urlpatterns = [
    path("menu-items/", views.menu_item_list, name="menu_item_list"),
    path("menu-items/add/", views.menu_item_create, name="menu_item_create"),
    path("menu-items/<int:pk>/edit/", views.menu_item_edit, name="menu_item_edit"),
    path("menu-items/<int:pk>/delete/", views.menu_item_delete, name="menu_item_delete"),
    path("menu-items/preview/", views.user_menu_preview, name="user_menu_preview"),
    path("menu-items/assign/group/", views.group_menu_assign, name="group_menu_assign"),
    path("menu-items/assign/user/", views.user_menu_assign, name="user_menu_assign"),
    path("menu-items/assign/user-group/", views.user_group_menu_assign, name="user_group_menu_assign"),
]
