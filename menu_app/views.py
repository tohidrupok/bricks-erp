from django.contrib import messages
from django.contrib.auth import get_user_model
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth.models import Group
from django.shortcuts import get_object_or_404, redirect, render

from .context_processors import user_can_see
from .forms import MenuItemForm
from .models import MenuItem, UserMenuOverride

User = get_user_model()


def _is_staff_or_super(user):
    return user.is_active and (user.is_superuser or user.is_staff)


# ---------------------------------------------------------------------------
# CRUD
# ---------------------------------------------------------------------------


# @login_required
# @user_passes_test(_is_staff_or_super)
# def user_group_menu_assign(request):
#     selected_user = None
#     selected_group = None
#     tree = []

#     user_id = request.POST.get("user_id") or request.GET.get("user_id")
#     group_id = request.POST.get("group_id") or request.GET.get("group_id")

#     if user_id:
#         selected_user = get_object_or_404(User, pk=user_id)
#     if group_id:
#         selected_group = get_object_or_404(Group, pk=group_id)

#     if request.method == "POST" and selected_user and selected_group:
#         selected_user.groups.add(selected_group)

#         checked_ids = set(request.POST.getlist("menu_items"))
#         for mi in MenuItem.objects.all():
#             should_have = str(mi.pk) in checked_ids
#             has_now = mi.groups.filter(pk=selected_group.pk).exists()
#             if should_have and not has_now:
#                 mi.groups.add(selected_group)
#             elif not should_have and has_now:
#                 mi.groups.remove(selected_group)

#         # Superuser restriction toggle
#         if selected_user.is_superuser:
#             restrict = request.POST.get("restrict_superuser") == "on"
#             UserMenuOverride.objects.update_or_create(
#                 user=selected_user, defaults={"restrict_superuser": restrict}
#             )

#         messages.success(
#             request,
#             f"{selected_user.get_username()} added to '{selected_group.name}' "
#             f"and menu access for that group updated."
#         )
#         return redirect(f"{request.path}?user_id={selected_user.pk}&group_id={selected_group.pk}")

#     if selected_group:
#         top_items = (
#             MenuItem.objects
#             .filter(parent__isnull=True)
#             .prefetch_related("children")
#             .order_by("order", "id")
#         )
#         for parent in top_items:
#             tree.append({
#                 "parent": parent,
#                 "parent_checked": parent.groups.filter(pk=selected_group.pk).exists(),
#                 "children": [
#                     {"item": c, "checked": c.groups.filter(pk=selected_group.pk).exists()}
#                     for c in parent.children.order_by("order", "id")
#                 ],
#             })

#     return render(request, "menu_app/user_group_menu_assign.html", {
#         "users": User.objects.filter(is_active=True).order_by("username"),
#         "groups": Group.objects.order_by("name"),
#         "selected_user": selected_user,
#         "selected_group": selected_group,
#         "user_current_groups": selected_user.groups.all() if selected_user else [],
#         "tree": tree,
#         "restrict_superuser": getattr(getattr(selected_user, "menu_override", None), "restrict_superuser", False),
#     })



@login_required
@user_passes_test(_is_staff_or_super)
def user_group_menu_assign(request):
    selected_user = None
    selected_groups = []
    tree = []

    user_id = request.POST.get("user_id") or request.GET.get("user_id")
    
    if user_id:
        selected_user = get_object_or_404(User, pk=user_id)

    if request.method == "POST" and selected_user:
        # Get list of selected group IDs from checkboxes
        group_ids = request.POST.getlist("groups")
        selected_groups = Group.objects.filter(pk__in=group_ids)
        
        # Update user's group memberships
        selected_user.groups.set(selected_groups)

        # Save menu items directly to the user's individual permissions
        checked_ids = set(request.POST.getlist("menu_items"))
        
        for mi in MenuItem.objects.all():
            should_have = str(mi.pk) in checked_ids
            has_user_now = mi.users.filter(pk=selected_user.pk).exists()
            
            if should_have and not has_user_now:
                mi.users.add(selected_user)
            elif not should_have and has_user_now:
                mi.users.remove(selected_user)

        messages.success(
            request,
            f"Access and departments for {selected_user.get_username()} updated successfully."
        )
        
        # Redirect back maintaining the user selection
        redirect_url = f"{request.path}?user_id={selected_user.pk}"
        return redirect(redirect_url)

    # If GET request, grab groups the user already belongs to
    if selected_user:
        selected_groups = selected_user.groups.all()
        
        top_items = (
            MenuItem.objects
            .filter(parent__isnull=True)
            .prefetch_related("children")
            .order_by("order", "id")
        )
        for parent in top_items:
            # Check if assigned directly to user OR through any of their selected/assigned groups
            parent_checked = (
                parent.users.filter(pk=selected_user.pk).exists() or
                parent.groups.filter(pk__in=selected_groups).exists()
            )
            
            children_list = []
            for c in parent.children.order_by("order", "id"):
                child_checked = (
                    c.users.filter(pk=selected_user.pk).exists() or
                    c.groups.filter(pk__in=selected_groups).exists()
                )
                children_list.append({"item": c, "checked": child_checked})

            tree.append({
                "parent": parent,
                "parent_checked": parent_checked,
                "children": children_list,
            })

    return render(request, "menu_app/user_group_menu_assign.html", {
        "users": User.objects.filter(is_active=True).order_by("username"),
        "groups": Group.objects.order_by("name"),
        "selected_user": selected_user,
        "selected_groups": selected_groups,
        "user_current_groups": selected_user.groups.all() if selected_user else [],
        "tree": tree,
    })



@login_required
@user_passes_test(_is_staff_or_super)
def menu_item_list(request):
    items = (
        MenuItem.objects
        .select_related("parent")
        .prefetch_related("groups", "users")
        .order_by("parent__order", "parent_id", "order", "id")
    )
    return render(request, "menu_app/menu_item_list.html", {"items": items})


@login_required
@user_passes_test(_is_staff_or_super)
def menu_item_create(request):
    if request.method == "POST":
        form = MenuItemForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Menu item created.")
            return redirect("menu_item_list")
    else:
        form = MenuItemForm()
    return render(request, "menu_app/menu_item_form.html", {"form": form, "title": "Add Menu Item"})


@login_required
@user_passes_test(_is_staff_or_super)
def menu_item_edit(request, pk):
    item = get_object_or_404(MenuItem, pk=pk)
    if request.method == "POST":
        form = MenuItemForm(request.POST, instance=item)
        if form.is_valid():
            form.save()
            messages.success(request, "Menu item updated.")
            return redirect("menu_item_list")
    else:
        form = MenuItemForm(instance=item)
    return render(request, "menu_app/menu_item_form.html", {"form": form, "title": "Edit Menu Item"})


@login_required
@user_passes_test(_is_staff_or_super)
def menu_item_delete(request, pk):
    item = get_object_or_404(MenuItem, pk=pk)
    if request.method == "POST":
        item.delete()
        messages.success(request, "Menu item deleted.")
        return redirect("menu_item_list")
    return render(request, "menu_app/menu_item_confirm_delete.html", {"item": item})


# ---------------------------------------------------------------------------
# Preview: what does a given user actually see right now
# ---------------------------------------------------------------------------

@login_required
@user_passes_test(_is_staff_or_super)
def user_menu_preview(request):
    selected_user = None
    visible_tree = []

    user_id = request.GET.get("user_id")
    if user_id:
        selected_user = get_object_or_404(User, pk=user_id)
        top_items = (
            MenuItem.objects
            .filter(parent__isnull=True, is_active=True)
            .prefetch_related("children")
            .order_by("order", "id")
        )
        for parent in top_items:
            visible_children = [
                child for child in parent.children.filter(is_active=True).order_by("order", "id")
                if user_can_see(child, selected_user)
            ]
            if user_can_see(parent, selected_user) or visible_children:
                visible_tree.append({"parent": parent, "children": visible_children})

    return render(request, "menu_app/user_menu_preview.html", {
        "users": User.objects.filter(is_active=True).order_by("username"),
        "selected_user": selected_user,
        "visible_tree": visible_tree,
    })


# ---------------------------------------------------------------------------
# Group-wise checkbox assignment (Accounts, HRM, Purchase, ...)
# ---------------------------------------------------------------------------

@login_required
@user_passes_test(_is_staff_or_super)
def group_menu_assign(request):
    selected_group = None
    tree = []

    group_id = request.POST.get("group_id") or request.GET.get("group_id")
    if group_id:
        selected_group = get_object_or_404(Group, pk=group_id)

    if request.method == "POST" and selected_group:
        checked_ids = set(request.POST.getlist("menu_items"))
        for mi in MenuItem.objects.all():
            should_have = str(mi.pk) in checked_ids
            has_now = mi.groups.filter(pk=selected_group.pk).exists()
            if should_have and not has_now:
                mi.groups.add(selected_group)
            elif not should_have and has_now:
                mi.groups.remove(selected_group)
        messages.success(request, f"Menu access updated for group '{selected_group.name}'.")
        return redirect(f"{request.path}?group_id={selected_group.pk}")

    if selected_group:
        top_items = (
            MenuItem.objects
            .filter(parent__isnull=True)
            .prefetch_related("children")
            .order_by("order", "id")
        )
        for parent in top_items:
            tree.append({
                "parent": parent,
                "parent_checked": parent.groups.filter(pk=selected_group.pk).exists(),
                "children": [
                    {"item": c, "checked": c.groups.filter(pk=selected_group.pk).exists()}
                    for c in parent.children.order_by("order", "id")
                ],
            })

    return render(request, "menu_app/group_menu_assign.html", {
        "groups": Group.objects.order_by("name"),
        "selected_group": selected_group,
        "tree": tree,
    })


# ---------------------------------------------------------------------------
# User-wise checkbox assignment (overrides group access for one person)
# ---------------------------------------------------------------------------

@login_required
@user_passes_test(_is_staff_or_super)
def user_menu_assign(request):
    selected_user = None
    tree = []

    user_id = request.POST.get("user_id") or request.GET.get("user_id")
    if user_id:
        selected_user = get_object_or_404(User, pk=user_id)

    if request.method == "POST" and selected_user:
        checked_ids = set(request.POST.getlist("menu_items"))
        for mi in MenuItem.objects.all():
            should_have = str(mi.pk) in checked_ids
            has_now = mi.users.filter(pk=selected_user.pk).exists()
            if should_have and not has_now:
                mi.users.add(selected_user)
            elif not should_have and has_now:
                mi.users.remove(selected_user)
        messages.success(request, f"Menu access updated for {selected_user.get_username()}.")
        return redirect(f"{request.path}?user_id={selected_user.pk}")

    if selected_user:
        top_items = (
            MenuItem.objects
            .filter(parent__isnull=True)
            .prefetch_related("children")
            .order_by("order", "id")
        )
        for parent in top_items:
            tree.append({
                "parent": parent,
                "parent_checked": parent.users.filter(pk=selected_user.pk).exists(),
                "children": [
                    {"item": c, "checked": c.users.filter(pk=selected_user.pk).exists()}
                    for c in parent.children.order_by("order", "id")
                ],
            })

    return render(request, "menu_app/user_menu_assign.html", {
        "users": User.objects.filter(is_active=True).order_by("username"),
        "selected_user": selected_user,
        "tree": tree,
    })
