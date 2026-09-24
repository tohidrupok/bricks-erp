from .models import MenuItem


def user_can_see(item, user):
    """Priority: specific users -> specific groups -> permission fallback -> deny.
    Superusers see everything UNLESS they have a UserMenuOverride with
    restrict_superuser=True, in which case they follow normal rules too."""
    if not user or not user.is_authenticated:
        return False

    if user.is_superuser:
        override = getattr(user, "menu_override", None)
        if not override or not override.restrict_superuser:
            return True
        # else: fall through and check like a normal user

    if item.users.exists():
        return item.users.filter(pk=user.pk).exists()

    if item.groups.exists():
        user_group_ids = user.groups.values_list("id", flat=True)
        return item.groups.filter(pk__in=user_group_ids).exists()

    if item.permission:
        return user.has_perm(item.permission)

    return False  # unconfigured item -> hidden by default for normal users


def build_sidebar_tree(user):
    """Core logic, usable from anywhere (context processor, template tag,
    a view, a management command debug script, ...). Always recomputed
    fresh per call — no caching, so group/permission changes take effect
    on the user's next page load."""
    if not user or not user.is_authenticated:
        return []

    top_items = (
        MenuItem.objects
        .filter(parent__isnull=True, is_active=True)
        .prefetch_related("children")
        .order_by("order", "id")
    )

    tree = []
    for parent in top_items:
        children = [
            {"title": c.title, "icon": c.icon, "url": c.url_name}
            for c in parent.children.filter(is_active=True).order_by("order", "id")
            if user_can_see(c, user)
        ]
        if user_can_see(parent, user) or children:
            tree.append({
                "title": parent.title,
                "icon": parent.icon,
                "url": parent.url_name,
                "children": children,
            })

    return tree


def sidebar_menu(request):
    """Django context processor entry point. Kept for backward compatibility
    with any template still relying on the context-processor-injected
    `sidebar_menu` variable — but menu_app/sidebar.html no longer depends
    on this being registered; it calls {% get_sidebar_menu %} directly."""
    user = getattr(request, "user", None)
    return {"sidebar_menu": build_sidebar_tree(user)}
