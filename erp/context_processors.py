from django.contrib.auth.models import Group

def sidebar_menu(request):
    """
    Adds to every template's context:
        menu_groups -> set of lowercase group names the user belongs to
        menu_perms  -> set of "app_label.codename" strings for every
                       permission the user has (via groups or directly)
    """
    if not request.user.is_authenticated:
        return {"menu_groups": set(), "menu_perms": set()}

    user = request.user

    if user.is_superuser:
        # Superusers see every section and pass every permission check.
        all_groups = set(
            name.lower() for name in Group.objects.values_list("name", flat=True)
        )
        all_perms = set(user.get_all_permissions())
        return {"menu_groups": all_groups, "menu_perms": all_perms}

    groups = set(
        name.lower() for name in user.groups.values_list("name", flat=True)
    )
    
    # FIXED: If the user has no groups (e.g. Burhan), read STRICTLY from 
    # direct user_permissions instead of get_all_permissions() to prevent 
    # unwanted app-wide permission bloat.
    if not groups:
        perms = set(
            f"{p.content_type.app_label}.{p.codename}" 
            for p in user.user_permissions.select_related('content_type').all()
        )
    else:
        perms = set(user.get_all_permissions())

    return {"menu_groups": groups, "menu_perms": perms}


def debug_user_permissions(request):
    user = request.user
    if not user.is_authenticated:
        return "Not logged in"
    
    context = {
        "username": user.username,
        "is_superuser": user.is_superuser,
        "groups": list(user.groups.values_list('name', flat=True)),
        "all_permissions": list(user.get_all_permissions()),
    }
    print(context) # Check your terminal output
    return context