"""
One-time data migration: Product used to carry a single `warehouse` +
`quantity_available` pair, which every GRN confirmation overwrote — so a
product received into two different warehouses silently lost whichever
warehouse's stock wasn't the most recent. Product now carries a `stock` list
(one entry per warehouse, see product_Items.models.WarehouseStock).

This rebuilds that list from scratch by replaying every Confirmed GRN in
order — the GRN documents themselves were never wrong, only the rolled-up
Product record was — so this recovers the warehouse split that the old
model had been quietly discarding. Draft/Rejected GRNs are not replayed.

Usage:
    python manage.py rebuild_product_stock
"""
from django.core.management.base import BaseCommand
from mongoengine.connection import get_db

from mysite.grn_models import GRN
from product_Items.models import Product


class Command(BaseCommand):
    help = 'Rebuild Product.stock (per-warehouse qty/price) by replaying every Confirmed GRN; drops the old single warehouse/quantity_available fields.'

    def handle(self, *args, **options):
        db = get_db()
        products_coll = db['products']

        # Raw update: the ODM can't load documents that still carry the now-
        # removed `warehouse`/`quantity_available` keys (MongoEngine's
        # default strict mode rejects unknown fields), so this first pass
        # has to go around the ODM.
        result = products_coll.update_many({}, {'$unset': {'warehouse': '', 'quantity_available': ''}, '$set': {'stock': []}})
        self.stdout.write(f'  Cleared legacy fields on {result.modified_count} product(s).')

        applied = 0
        grns = GRN.objects(status='Confirmed').order_by('created_at')
        for grn in grns:
            if not grn.warehouse:
                continue
            for item in grn.items:
                product = item.product
                if not product:
                    continue
                product.receive_stock(grn.warehouse, item.received_qty, item.unit_price)
                product.save()
                applied += 1
            self.stdout.write(f'  Replayed {grn.grn_number} -> {grn.warehouse.warehouse_name}')

        self.stdout.write(self.style.SUCCESS(f'Done. Replayed {applied} GRN line item(s) across {grns.count()} confirmed GRN(s).'))
