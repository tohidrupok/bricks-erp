"""
core/context_processors.py

Makes a `menu_groups` set available in EVERY template automatically,
so the sidebar can do:

    {% if "hrm" in menu_groups %} ... {% endif %}

instead of the old:

    {% if request.session.department == "hrm" %} ... {% endif %}

This is driven 100% by Django's built-in auth Groups (Auth > Users > Groups
in /admin/), exactly like the screenshot you shared:
  - "Chosen groups" on a user  ->  which sidebar SECTIONS show for that user
  - "Chosen user permissions"  ->  (optional, finer-grained) which individual
                                     links inside a section show

No custom session/department field needs to be set at login anymore.
"""

from django.contrib.auth.models import Group


def menu_permissions(request):
    """
    Adds:
        menu_groups  -> a set of lowercase group names the user belongs to
                         e.g. {"hrm", "accounts"}  (superusers get every group)
    to the context of every template.
    """
    if not request.user.is_authenticated:
        return {"menu_groups": set()}

    user = request.user

    if user.is_superuser:
        # Superusers should see the full sidebar regardless of which
        # groups they were actually added to.
        all_groups = set(
            name.lower() for name in Group.objects.values_list("name", flat=True)
        )
        return {"menu_groups": all_groups}

    groups = set(
        name.lower() for name in user.groups.values_list("name", flat=True)
    )
    return {"menu_groups": groups}
