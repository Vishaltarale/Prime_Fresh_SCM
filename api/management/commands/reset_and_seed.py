"""
Wipes every MongoEngine collection in the project and seeds one demo login
per role in the new consolidated api.models.User (the auth the React web/
mobile apps actually use). The old app's two legacy login realms
(mysite.admin1, Users.User1) are cleared but intentionally left unseeded —
they use unhashed passwords and are being phased out.

Usage:
    python manage.py reset_and_seed          # wipe + seed
    python manage.py reset_and_seed --no-seed  # wipe only
"""
from django.core.management.base import BaseCommand

from api.models import User as ApiUser
from mysite.models import Student, admin1, FruitInventory, Employee, Farmer, Supplier, Customer
from mysite.grn_models import GRN
from Orders.models import Order
from product_Items.models import Category, Subcategory, Product
from Location.models import Warehouse
from UOM.models import UOM, UOMConversionMatrix
from Users.models import User1

ALL_MODELS = [
    Student, admin1, FruitInventory, Employee, Farmer, Supplier, Customer,
    GRN, Order, Category, Subcategory, Product, Warehouse,
    UOM, UOMConversionMatrix, User1, ApiUser,
]

SEED_ACCOUNTS = [
    {'full_name': 'Admin User', 'email': 'admin@primefresh.com', 'phone': '9000000001', 'password': 'Admin@12345', 'role': 'Admin'},
    {'full_name': 'Inventory Officer', 'email': 'inventory@primefresh.com', 'phone': '9000000002', 'password': 'Inventory@12345', 'role': 'Inventory Officer'},
    {'full_name': 'Warehouse Manager', 'email': 'warehouse@primefresh.com', 'phone': '9000000003', 'password': 'Warehouse@12345', 'role': 'Warehouse Manager'},
]


class Command(BaseCommand):
    help = 'Wipe all business data and seed one demo login per role (for client handoff / fresh environments).'

    def add_arguments(self, parser):
        parser.add_argument('--no-seed', action='store_true', help='Wipe only, skip creating demo accounts.')
        parser.add_argument('--yes', action='store_true', help='Skip the confirmation prompt.')

    def handle(self, *args, **options):
        if not options['yes']:
            confirm = input(
                'This will PERMANENTLY DELETE all data in every collection '
                '(orders, GRNs, products, users, everything). Type "wipe" to continue: '
            )
            if confirm.strip().lower() != 'wipe':
                self.stdout.write(self.style.WARNING('Aborted — no changes made.'))
                return

        for model in ALL_MODELS:
            count = model.objects.count()
            model.objects.delete()
            self.stdout.write(f'  Cleared {model.__name__}: {count} document(s) deleted.')

        self.stdout.write(self.style.SUCCESS('Database wiped.'))

        if options['no_seed']:
            return

        self.stdout.write('')
        self.stdout.write('Seeding demo accounts (new API auth only)...')
        for acct in SEED_ACCOUNTS:
            user = ApiUser(full_name=acct['full_name'], email=acct['email'], phone=acct['phone'], role=acct['role'])
            user.set_password(acct['password'])
            user.save()
            self.stdout.write(f"  {acct['role']:<20} {acct['email']:<28} password: {acct['password']}")

        self.stdout.write(self.style.SUCCESS('Done. Hand the above credentials to the client.'))
