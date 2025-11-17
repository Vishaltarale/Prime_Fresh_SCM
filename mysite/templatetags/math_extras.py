# your_app/templatetags/math_extras.py

from django import template

register = template.Library()

@register.filter
def multiply(value, arg):
    try:
        return float(value) * float(arg)
    except (ValueError, TypeError):
        return 0

@register.filter
def get_total(items):
    total = 0
    for item in items:
        try:
            total += float(item.price) * float(item.quantity)
        except (AttributeError, ValueError, TypeError):
            continue
    return round(total, 2)
