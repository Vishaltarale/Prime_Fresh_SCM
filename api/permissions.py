from rest_framework.permissions import BasePermission, SAFE_METHODS

from .models import STAFF_ROLES


def has_role(*allowed_roles):
    """Factory: build a DRF permission class restricting access to the given roles."""

    class _RolePermission(BasePermission):
        def has_permission(self, request, view):
            user = request.user
            return bool(user and user.is_authenticated and user.role in allowed_roles)

    return _RolePermission


# Named role groups, matching the module-access matrix:
#   Admin               — everything
#   Inventory Officer    — GRN + Products/Catalog only
#   Warehouse Manager    — GRN + Products/Catalog + Orders + Reports
#   Customer             — own Orders/invoices only, browse products, own profile
#   Supplier / Farmer    — own GRN deliveries (read-only), own profile
IsAdmin = has_role('Admin')
IsStaff = has_role(*STAFF_ROLES)
IsCatalogStaff = has_role(*STAFF_ROLES)  # GRN + catalog: all three staff roles
IsOrdersStaff = has_role('Admin', 'Warehouse Manager')
IsReportsStaff = has_role('Admin', 'Warehouse Manager')
IsCustomer = has_role('Customer')
IsSupplier = has_role('Supplier')
IsFarmer = has_role('Farmer')
IsSupplierOrFarmer = has_role('Supplier', 'Farmer')


class IsStaffOrReadOnly(BasePermission):
    """Any authenticated user may read (browse the catalog); only staff may write."""

    def has_permission(self, request, view):
        user = request.user
        if not (user and user.is_authenticated):
            return False
        if request.method in SAFE_METHODS:
            return True
        return user.role in STAFF_ROLES


def get_linked_entity(user):
    """
    Resolve the Customer/Supplier/Farmer document that corresponds to an
    external-role user, matched by email (both sides have unique emails).
    Self-registration creates both records with the same email, so this
    lookup is how a Customer/Supplier/Farmer login is scoped to "their own"
    orders/deliveries without a separate foreign key.
    """
    from mysite.models import Customer, Supplier, Farmer

    if user.role == 'Customer':
        return Customer.objects(email=user.email).first()
    if user.role == 'Supplier':
        return Supplier.objects(email=user.email).first()
    if user.role == 'Farmer':
        return Farmer.objects(email=user.email).first()
    return None
