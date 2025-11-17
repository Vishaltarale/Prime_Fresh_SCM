# your_app/templatetags/custom_tags.py
from django import template
from django.shortcuts import redirect
from functools import wraps

register = template.Library()

@register.filter
def get_attribute(obj, attr):
    return getattr(obj, attr, '')

def login_required_custom(view_func):
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if not request.session.get('user_email'):
            return redirect("user_login")  # Replace with your login URL name
        return view_func(request, *args, **kwargs)
    return wrapper


from django import template

register = template.Library()

@register.filter(name='get_attribute')
def get_attribute(obj, attr):
    """
    Get an attribute from an object dynamically.
    Usage: {{ obj|get_attribute:"field_name" }}
    """
    try:
        if hasattr(obj, attr):
            value = getattr(obj, attr, None)
            # Handle MongoEngine ReferenceField
            if hasattr(value, '__call__'):
                value = value()
            # Convert to string if it's an object
            if hasattr(value, '__str__') and not isinstance(value, (str, int, float, bool)):
                return str(value)
            return value if value is not None else "N/A"
        return "N/A"
    except Exception:
        return "N/A"


@register.filter(name='index')
def index(sequence, position):
    """
    Get an item from a sequence by index.
    Usage: {{ list|index:0 }}
    """
    try:
        return sequence[position]
    except (IndexError, TypeError, KeyError):
        return ""


@register.filter(name='replace')
def replace(value, arg):
    """
    Replace characters in a string.
    Usage: {{ value|replace:"_: " }}
    """
    if not value:
        return value
    
    try:
        old, new = arg.split(':')
        return value.replace(old, new)
    except (ValueError, AttributeError):
        return value


from django import template

register = template.Library()

@register.filter(name='get_attribute')
def get_attribute(obj, attr):
    """
    Get an attribute from an object dynamically.
    Usage: {{ obj|get_attribute:"field_name" }}
    """
    try:
        if hasattr(obj, attr):
            value = getattr(obj, attr, None)
            # Handle MongoEngine ReferenceField
            if hasattr(value, '__call__'):
                value = value()
            # Convert to string if it's an object
            if hasattr(value, '__str__') and not isinstance(value, (str, int, float, bool)):
                return str(value)
            return value if value is not None else "N/A"
        return "N/A"
    except Exception:
        return "N/A"


@register.filter(name='attr')
def attr(obj, attr):
    """
    Simple attribute getter for forms.
    Usage: {{ obj|attr:"field_name" }}
    """
    try:
        return getattr(obj, attr, '')
    except Exception:
        return ''


@register.filter(name='index')
def index(sequence, position):
    """
    Get an item from a sequence by index.
    Usage: {{ list|index:0 }}
    """
    try:
        return sequence[position]
    except (IndexError, TypeError, KeyError):
        return ""


@register.filter(name='replace')
def replace(value, arg):
    """
    Replace characters in a string.
    Usage: {{ value|replace:"_: " }}
    """
    if not value:
        return value
    
    try:
        old, new = arg.split(':')
        return value.replace(old, new)
    except (ValueError, AttributeError):
        return value