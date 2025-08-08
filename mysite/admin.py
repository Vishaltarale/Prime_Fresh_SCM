from django_mongoengine import mongo_admin as admin
from .models import Student

class StudentAdmin(admin.DocumentAdmin):
    pass

admin.site.register(Student, StudentAdmin)