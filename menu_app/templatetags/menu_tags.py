from django import template
from menu_app.models import MenuItem
from menu_app.context_processors import user_can_see

register = template.Library()

@register.simple_tag(takes_context=True)
def get_sidebar_menu(context):
    request = context['request']
    user = request.user

    visible_tree = []
    
    # Get active top-level menu items ordered by 'order'
    top_items = (
        MenuItem.objects
        .filter(parent__isnull=True, is_active=True)
        .prefetch_related("children")
        .order_by("order", "id")
    )

    for parent in top_items:
        # Get active children and filter them using user_can_see
        visible_children = [
            child for child in parent.children.filter(is_active=True).order_by("order", "id")
            if user_can_see(child, user)
        ]
        
        # Include the parent if the user has permission for the parent OR if they can see at least one child
        if user_can_see(parent, user) or visible_children:
            visible_tree.append({
                "title": parent.title,
                "url": getattr(parent, 'url_name', '') or getattr(parent, 'url', ''),
                "icon": parent.icon,
                "children": [
                    {
                        "title": c.title,
                        "url": getattr(c, 'url_name', '') or getattr(c, 'url', ''),
                        "icon": c.icon,
                    }
                    for c in visible_children
                ]
            })

    return visible_tree