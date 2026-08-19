"""
Notification creation helpers, called from the places that actually change
state (GRN confirm, order completion, PO status transitions) — kept here so
those views don't each reimplement de-duplication/resolution logic.
"""
from .notification_models import Notification

LOW_STOCK_THRESHOLD = 10


def sync_low_stock_alert(product, warehouse):
    """
    Call after any stock mutation (GRN receive, order completion) for a
    given (product, warehouse). Creates a warning/critical alert if the
    resulting quantity is at/below threshold and none is already open;
    auto-resolves the existing one if stock has since recovered above it —
    so alerts reflect current reality instead of accumulating forever.
    """
    if not product or not warehouse:
        return
    line = product.get_stock(warehouse)
    qty = line.quantity_available if line else 0

    existing = Notification.objects(category='low_stock', product=product, warehouse=warehouse, resolved=False).first()

    if qty <= LOW_STOCK_THRESHOLD:
        if existing:
            # Refresh severity/message in case qty dropped further since it was raised.
            existing.severity = 'critical' if qty <= LOW_STOCK_THRESHOLD // 2 else 'warning'
            existing.message = f'{product.name} is down to {qty} units in {warehouse.warehouse_name}.'
            existing.save()
            return
        Notification(
            category='low_stock',
            severity='critical' if qty <= LOW_STOCK_THRESHOLD // 2 else 'warning',
            title='Low stock',
            message=f'{product.name} is down to {qty} units in {warehouse.warehouse_name}.',
            warehouse=warehouse,
            product=product,
        ).save()
    elif existing:
        existing.resolved = True
        existing.save()


def notify_status(category, title, message, severity='info', po_id=None, grn_id=None):
    """General-purpose status notification (PO sent/confirmed/rejected, GRN confirmed/rejected, ...)."""
    Notification(
        category=category, severity=severity, title=title, message=message,
        po_id=str(po_id) if po_id else None, grn_id=str(grn_id) if grn_id else None,
    ).save()
