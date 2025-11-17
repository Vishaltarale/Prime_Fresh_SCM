# users/decorators.py
from functools import wraps
from django.shortcuts import redirect

def role_required(allowed_roles):
    def decorator(view_func):
        @wraps(view_func)
        def wrapper(request, *args, **kwargs):
            if not getattr(request, "user", None):
                return redirect("login")
            if request.user.role.name not in allowed_roles:
                return redirect("unauthorized")
            return view_func(request, *args, **kwargs)
        return wrapper
    return decorator


# === Predefined Decorators per Module ===

dashboard_access = role_required(["admin", "inventory_manager", "purchase_manager", "order_manager", "warehouse_manager", "report_viewer", "staff"])

inventory_access = role_required(["admin", "inventory_manager", "warehouse_manager"])
purchase_access = role_required(["admin", "purchase_manager"])
orders_access = role_required(["admin", "order_manager"])
suppliers_access = role_required(["admin", "purchase_manager"])
warehouse_access = role_required(["admin", "inventory_manager", "warehouse_manager"])
reports_access = role_required(["admin", "inventory_manager", "purchase_manager", "order_manager", "report_viewer"])
settings_access = role_required(["admin"])
