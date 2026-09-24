"""
menu_app/models.py

One row = one sidebar entry (a dropdown section OR a clickable link).
Everything about the sidebar — what exists, its order, its icon, and
who can see it — lives here and is editable from /admin/, or from the
group/user assignment screens in menu_app/views.py. No template edits
needed to add, remove, rename, or re-permission a menu item.

Visibility is controlled two ways, checked in this priority order by
menu_app/context_processors.py:
  1. `users`      -> if any specific users are selected, the item is visible
                     to that specific user.
  2. `groups`     -> if any groups are selected, the item is visible to
                     a user who belongs to at least ONE of them
                     (works for a single group or several).
  3. `permission` -> fallback, only checked if `groups` and `users` are empty.
                     Exact Django permission codename, "app_label.codename".
  4. All blank    -> hidden for normal users (unconfigured default deny),
                     visible only to superusers.
Superusers always see every item regardless of the above, unless they
have a UserMenuOverride with restrict_superuser=True (see below).

Structure is limited to 2 levels (top-level section -> child link).
A child cannot itself have children — enforced in clean() below, since
the sidebar/context-processor logic only ever walks one level deep.

IMPORTANT for menu_app/management/commands/seed_menu.py:
Rows are matched on (title, parent, url_name) via update_or_create.
Two DATA entries that share the same title + parent + url will
collide and overwrite each other. Keep top-level titles unique
(e.g. "Document (Office)" vs "Document (Restaurant)") if they'd
otherwise share an empty url_name under the same parent.
"""

from django.conf import settings
from django.contrib.auth.models import Group
from django.core.exceptions import ValidationError
from django.db import models


class MenuItem(models.Model):
    title = models.CharField(
        max_length=100,
        help_text="Label shown in the sidebar, e.g. 'Employee Document'",
    )
    icon = models.CharField(
        max_length=50,
        blank=True,
        default="circle",
        help_text="Lucide icon name used elsewhere in the UI, e.g. 'activity', 'home'",
    )
    url_name = models.CharField(
        max_length=100,
        blank=True,
        help_text=(
            "Django URL name used in {% url %}, e.g. 'employee_list'. "
            "Leave blank if this row is only a dropdown parent (has children)."
        ),
    )
    parent = models.ForeignKey(
        "self",
        null=True,
        blank=True,
        on_delete=models.CASCADE,
        related_name="children",
        help_text="Leave blank for a top-level section (e.g. 'HRM'). "
        "Set to a parent row for a link that lives inside a dropdown.",
    )
    permission = models.CharField(
        max_length=150,
        blank=True,
        help_text=(
            "Optional fallback, only used if no Groups or Users are selected below. "
            "Exact Django permission codename, e.g. 'accounting.view_creditvoucher' "
            "(app_label.codename — same format shown in the 'Chosen user "
            "permissions' box in /admin/)."
        ),
    )
    users = models.ManyToManyField(
        settings.AUTH_USER_MODEL,
        blank=True,
        related_name="menu_items",
        help_text=(
            "Which specific user(s) can see this item — pick one or several. "
            "Superusers always see every item regardless of this field."
        ),
    )
    groups = models.ManyToManyField(
        Group,
        blank=True,
        related_name="menu_items",
        help_text=(
            "Which group(s) can see this item — pick one or several. "
            "Superusers always see every item regardless of this field."
        ),
    )
    order = models.PositiveIntegerField(default=0)
    is_active = models.BooleanField(
        default=True,
        help_text="Untick to hide this item for everyone without deleting it.",
    )

    class Meta:
        ordering = ["order", "id"]

    def __str__(self):
        if self.parent_id:
            return f"{self.parent.title} → {self.title}"
        return self.title

    def clean(self):
        super().clean()
        errors = {}

        if self.parent_id and self.pk and self.parent_id == self.pk:
            errors["parent"] = "A menu item cannot be its own parent."

        # Only 2 levels are supported: top-level section -> child link.
        # If the chosen parent itself has a parent, this row would become
        # a grandchild that the sidebar/context-processor never renders.
        if self.parent_id and not errors.get("parent"):
            if self.parent.parent_id:
                errors["parent"] = (
                    "Menu only supports 2 levels. "
                    f"'{self.parent.title}' is already a child of "
                    f"'{self.parent.parent.title}' and cannot have its own children."
                )

        if errors:
            raise ValidationError(errors)

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)


class UserMenuOverride(models.Model):
    """Only meaningful for superusers. If restrict_superuser is True,
    this superuser's sidebar follows normal group/user menu rules
    instead of auto-seeing every item."""

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="menu_override",
        limit_choices_to={"is_superuser": True},
    )
    restrict_superuser = models.BooleanField(
        default=False,
        help_text=(
            "Tick to make this superuser's sidebar follow normal group/user "
            "rules instead of showing everything."
        ),
    )

    def __str__(self):
        return f"{self.user.get_username()} (restricted: {self.restrict_superuser})"
