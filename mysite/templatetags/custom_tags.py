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



