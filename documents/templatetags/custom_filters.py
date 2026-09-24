# documents/templatetags/custom_filters.py

from django import template

register = template.Library()

@register.filter(name='endswith')
def endswith(value, arg):
    """Returns True if the string ends with the given suffix"""
    return value.endswith(arg)
