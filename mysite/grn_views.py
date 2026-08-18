from django.shortcuts import render, redirect
from django.contrib import messages
from django.utils import timezone
from datetime import datetime
import uuid

from .grn_models import GRN, GRNItem
from product_Items.models import Product
from Location.models import Warehouse
from mysite.models import Supplier, Farmer


def _login_required(request):
    """Return redirect if user not logged in, else None."""
    if not request.session.get('user_email'):
        return redirect('Users:login_user')
    return None


def _next_grn_number():
    """Generate a sequential GRN number like GRN-20260625-0042."""
    date_str = datetime.utcnow().strftime('%Y%m%d')
    count = GRN.objects.count() + 1
    return f"GRN-{date_str}-{count:04d}"


# ── List all GRNs ────────────────────────────────────────────────────────────
def grn_list(request):
    guard = _login_required(request)
    if guard:
        return guard

    status_filter = request.GET.get('status', '')
    grns = GRN.objects.all()
    if status_filter:
        grns = grns.filter(status=status_filter)

    return render(request, 'grn_list.html', {
        'grns': grns,
        'status_filter': status_filter,
        'status_options': ['All'] + list(GRN.GRN_STATUS),
    })


# ── Create new GRN ───────────────────────────────────────────────────────────
def grn_create(request):
    guard = _login_required(request)
    if guard:
        return guard

    products   = Product.objects.all()
    warehouses = Warehouse.objects.all()
    suppliers  = Supplier.objects.all()
    farmers    = Farmer.objects.all()

    if request.method == 'POST':
        source_type  = request.POST.get('source_type')
        warehouse_id = request.POST.get('warehouse')
        notes        = request.POST.get('notes', '')
        status       = request.POST.get('status', 'Draft')

        # Resolve source reference
        supplier = farmer = None
        if source_type == 'Supplier':
            sid = request.POST.get('supplier_id')
            if sid:
                supplier = Supplier.objects(id=sid).first()
        elif source_type == 'Farmer':
            fid = request.POST.get('farmer_id')
            if fid:
                farmer = Farmer.objects(id=fid).first()

        warehouse = Warehouse.objects(id=warehouse_id).first()

        # Build line items from repeated POST fields
        product_ids   = request.POST.getlist('product_id[]')
        ordered_qtys  = request.POST.getlist('ordered_qty[]')
        received_qtys = request.POST.getlist('received_qty[]')
        unit_prices   = request.POST.getlist('unit_price[]')
        uoms          = request.POST.getlist('uom[]')
        remarks_list  = request.POST.getlist('remarks[]')

        items = []
        total = 0.0
        for i in range(len(product_ids)):
            if not product_ids[i]:
                continue
            product = Product.objects(id=product_ids[i]).first()
            if not product:
                continue
            o_qty  = int(ordered_qtys[i]  or 0)
            r_qty  = int(received_qtys[i] or 0)
            price  = float(unit_prices[i] or 0)
            line   = GRNItem(
                product=product,
                ordered_qty=o_qty,
                received_qty=r_qty,
                unit_price=price,
                uom=uoms[i] if i < len(uoms) else '',
                remarks=remarks_list[i] if i < len(remarks_list) else '',
            )
            items.append(line)
            total += r_qty * price

            # Update product stock if confirming
            if status == 'Confirmed':
                product.quantity_available += r_qty
                product.save()

        grn = GRN(
            grn_number=_next_grn_number(),
            source_type=source_type,
            supplier=supplier,
            farmer=farmer,
            warehouse=warehouse,
            items=items,
            total_amount=total,
            status=status,
            received_by=request.session.get('user_email', ''),
            notes=notes,
        )
        grn.save()
        messages.success(request, f"GRN '{grn.grn_number}' created successfully.")
        return redirect('mysite:grn_list')

    return render(request, 'grn_form.html', {
        'products': products,
        'warehouses': warehouses,
        'suppliers': suppliers,
        'farmers': farmers,
        'mode': 'create',
    })


# ── View a single GRN ────────────────────────────────────────────────────────
def grn_detail(request, grn_id):
    guard = _login_required(request)
    if guard:
        return guard

    grn = GRN.objects(id=grn_id).first()
    if not grn:
        return redirect('mysite:grn_list')

    return render(request, 'grn_detail.html', {'grn': grn})


# ── Confirm a Draft GRN (updates stock) ─────────────────────────────────────
def grn_confirm(request, grn_id):
    guard = _login_required(request)
    if guard:
        return guard

    grn = GRN.objects(id=grn_id).first()
    if grn and grn.status == 'Draft':
        for item in grn.items:
            product = item.product
            if product:
                product.quantity_available += item.received_qty
                product.save()
        grn.status = 'Confirmed'
        grn.save()
        messages.success(request, f"GRN '{grn.grn_number}' confirmed — stock updated.")
    elif grn:
        messages.warning(request, f"GRN '{grn.grn_number}' can't be confirmed — it's already {grn.status}.")
    else:
        messages.error(request, "GRN not found.")

    return redirect('mysite:grn_detail', grn_id=grn_id)


# ── Reject a Draft GRN ───────────────────────────────────────────────────────
def grn_reject(request, grn_id):
    guard = _login_required(request)
    if guard:
        return guard

    grn = GRN.objects(id=grn_id).first()
    if grn and grn.status == 'Draft':
        grn.status = 'Rejected'
        grn.save()
        messages.error(request, f"GRN '{grn.grn_number}' rejected.", extra_tags="critical")
    elif grn:
        messages.warning(request, f"GRN '{grn.grn_number}' can't be rejected — it's already {grn.status}.")
    else:
        messages.error(request, "GRN not found.")

    return redirect('mysite:grn_detail', grn_id=grn_id)
