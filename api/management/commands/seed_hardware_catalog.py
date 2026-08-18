"""
Seeds a small hardware catalog (cameras, PCs/servers) sourced from a
supplier only — no Farmer involvement, since this stock isn't farm produce.

Creates, per run (idempotent — re-running won't duplicate anything):
    - 1 Supplier   (the sole source for this catalog)
    - 1 Warehouse  (where the stock sits)
    - 2 UOM        (PCS, BOX — needed to express the conversion matrix)
    - 2 UOMConversionMatrix entries (BOX <-> PCS, both directions)
    - 2 Category   (Cameras, Computer Hardware)
    - 2 Subcategory (one per category)
    - 2 Product    (a camera, a server) — supplier set, farmer left unset

Usage:
    python manage.py seed_hardware_catalog
"""
from datetime import date

from django.core.management.base import BaseCommand

from mysite.models import Supplier
from Location.models import Warehouse
from UOM.models import UOM, UOMConversionMatrix
from product_Items.models import Category, Subcategory, Product


class Command(BaseCommand):
    help = 'Seed a supplier-sourced hardware catalog: 2 categories, 2 subcategories, 2 UOM conversion matrix entries, 2 products.'

    def handle(self, *args, **options):
        supplier = self._get_or_create_supplier()
        warehouse = self._get_or_create_warehouse()
        pcs, box = self._get_or_create_uoms()
        self._get_or_create_matrix(pcs, box)
        cameras, computer_hardware = self._get_or_create_categories()
        cctv_sub, server_sub = self._get_or_create_subcategories(cameras, computer_hardware)
        self._get_or_create_products(cctv_sub, server_sub, pcs, warehouse, supplier)

        self.stdout.write(self.style.SUCCESS('Hardware catalog seeded.'))

    def _get_or_create_supplier(self):
        supplier = Supplier.objects(email='sales@techsourcedist.com').first()
        if supplier:
            return supplier
        supplier = Supplier(
            supplier_name='Rahul Mehta',
            company_name='TechSource Distributors',
            email='sales@techsourcedist.com',
            phone='9123456780',
            address='Plot 14, Electronics Market',
            state='Maharashtra',
            district='Pune',
            registration_date=date.today(),
            verified=True,
        )
        supplier.save()
        self.stdout.write('  Created Supplier: TechSource Distributors')
        return supplier

    def _get_or_create_warehouse(self):
        warehouse = Warehouse.objects(warehouse_name='IT Hardware Warehouse').first()
        if warehouse:
            return warehouse
        warehouse = Warehouse(
            warehouse_name='IT Hardware Warehouse',
            address='Plot 22, Industrial Estate',
            city='Pune',
            state='Maharashtra',
            pincode='411019',
        )
        warehouse.save()
        self.stdout.write('  Created Warehouse: IT Hardware Warehouse')
        return warehouse

    def _get_or_create_uoms(self):
        pcs = UOM.objects(name='PCS').first()
        if not pcs:
            pcs = UOM(name='PCS', description='Pieces').save()
            self.stdout.write('  Created UOM: PCS')

        box = UOM.objects(name='BOX').first()
        if not box:
            box = UOM(name='BOX', description='Box of 5 units').save()
            self.stdout.write('  Created UOM: BOX')

        return pcs, box

    def _get_or_create_matrix(self, pcs, box):
        if not UOMConversionMatrix.objects(from_uom=box, to_uom=pcs).first():
            UOMConversionMatrix(from_uom=box, to_uom=pcs, factor=5).save()
            self.stdout.write('  Created UOM matrix: 1 BOX = 5 PCS')

        if not UOMConversionMatrix.objects(from_uom=pcs, to_uom=box).first():
            UOMConversionMatrix(from_uom=pcs, to_uom=box, factor=0.2).save()
            self.stdout.write('  Created UOM matrix: 1 PCS = 0.2 BOX')

    def _get_or_create_categories(self):
        cameras = Category.objects(name='Cameras').first()
        if not cameras:
            cameras = Category(name='Cameras', description='Surveillance and imaging hardware').save()
            self.stdout.write('  Created Category: Cameras')

        computer_hardware = Category.objects(name='Computer Hardware').first()
        if not computer_hardware:
            computer_hardware = Category(name='Computer Hardware', description='PCs, servers, and related equipment').save()
            self.stdout.write('  Created Category: Computer Hardware')

        return cameras, computer_hardware

    def _get_or_create_subcategories(self, cameras, computer_hardware):
        cctv_sub = Subcategory.objects(name='CCTV Cameras', category=cameras).first()
        if not cctv_sub:
            cctv_sub = Subcategory(name='CCTV Cameras', category=cameras).save()
            self.stdout.write('  Created Subcategory: CCTV Cameras (Cameras)')

        server_sub = Subcategory.objects(name='Servers & PCs', category=computer_hardware).first()
        if not server_sub:
            server_sub = Subcategory(name='Servers & PCs', category=computer_hardware).save()
            self.stdout.write('  Created Subcategory: Servers & PCs (Computer Hardware)')

        return cctv_sub, server_sub

    def _get_or_create_products(self, cctv_sub, server_sub, pcs, warehouse, supplier):
        if not Product.objects(sku='CAM-DOME-001').first():
            Product(
                name='4MP Dome CCTV Camera',
                sku='CAM-DOME-001',
                category=cctv_sub.category,
                subcategory=cctv_sub,
                uom=pcs,
                warehouse=warehouse,
                price_per_unit=2499.00,
                quantity_available=100,
                description='4MP indoor/outdoor dome CCTV camera with night vision.',
                supplier=supplier,
                farmer=None,
            ).save()
            self.stdout.write('  Created Product: 4MP Dome CCTV Camera')

        if not Product.objects(sku='SRV-RACK-001').first():
            Product(
                name='1U Rack Server',
                sku='SRV-RACK-001',
                category=server_sub.category,
                subcategory=server_sub,
                uom=pcs,
                warehouse=warehouse,
                price_per_unit=145000.00,
                quantity_available=20,
                description='1U rack-mount server, Xeon CPU, 32GB RAM, dual PSU.',
                supplier=supplier,
                farmer=None,
            ).save()
            self.stdout.write('  Created Product: 1U Rack Server')
