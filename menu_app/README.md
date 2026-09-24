# menu_app — install / wiring guide

## 1. settings.py

```python
INSTALLED_APPS = [
    ...
    "menu_app",
]

TEMPLATES = [
    {
        ...
        "OPTIONS": {
            "context_processors": [
                ...
                "menu_app.context_processors.sidebar_menu",
            ],
        },
    },
]
```

Missing the context processor line is the #1 cause of "sidebar shows nothing" —
it silently returns an empty list to every template, no error is raised.

## 2. Project urls.py

```python
from django.urls import path, include

urlpatterns = [
    path("admin/", admin.site.urls),
    path("", include("menu_app.urls")),
]
```

`menu_app/urls.py` has no `app_name` set, so use plain `{% url 'menu_item_list' %}`
(no namespace prefix) in templates, matching what's already written in the
templates here. If you add `namespace="menu_app"` to the include, you must also
add `menu_app:` in front of every `{% url %}` tag in every template in this app.

## 3. Migrate

```bash
python manage.py makemigrations menu_app
python manage.py migrate menu_app
```

If you're moving this into a project that already has an OLDER version of
MenuItem (e.g. one with a legacy `departments` CharField), check
`python manage.py dbshell` -> `.schema menu_app_menuitem` BEFORE migrating, to
confirm the live table matches this models.py. Mismatches between a stale DB
schema and a fresh models.py are what caused most of the migration issues in
this app's history — always diff schema vs model before trusting
`showmigrations`, since fake-applies or partially-run migrations can make
`showmigrations` show `[X]` for something that never actually ran.

## 4. Seed the menu

```bash
python manage.py seed_menu
```

Safe to re-run — matches existing rows on (title, parent, url_name) and
updates in place rather than duplicating.

## 5. Include the sidebar in your base template

```django
{% include "menu_app/sidebar.html" %}
```

Every `url_name` in your seeded MenuItem rows must correspond to a REAL
Django URL name currently in your urlconf. A typo or a since-removed URL name
will raise NoReverseMatch and can blank the whole page depending on where
the include sits — check any row seeded with url="" is a genuine dropdown
parent (has children), not a real link that's missing its url_name by mistake.

## 6. Give staff a way to manage the menu without /admin/

- `/menu-items/` — list, add, edit, delete individual menu rows.
- `/menu-items/assign/group/` — pick a Group (Accounts, HRM, Purchase, ...),
  check which menus/features that department can see.
- `/menu-items/assign/user/` — pick one user, check menus/features for them
  specifically. This OVERRIDES that item's group-based visibility for that
  user — per MenuItem's priority rule (users > groups > permission), checking
  any box here makes the item visible ONLY to users explicitly checked, not
  "this user plus their group." Use for individual exceptions, not routine
  department access.
- `/menu-items/preview/` — pick a user, see exactly what they'd see in the
  live sidebar right now, without logging in as them.

Restrict access to all of the above (they're already gated to staff/superuser
via `user_passes_test`, but also add MenuItem rows for these URLs themselves
so they show up in the sidebar for whoever should manage this).
