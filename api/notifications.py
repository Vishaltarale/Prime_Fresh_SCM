from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status as http_status

from .permissions import IsStaff
from .notification_models import Notification


def _serialize(n, user_email):
    return {
        'id': str(n.id),
        'category': n.category,
        'severity': n.severity,
        'title': n.title,
        'message': n.message,
        'warehouse': {'id': str(n.warehouse.id), 'name': n.warehouse.warehouse_name} if n.warehouse else None,
        'product': {'id': str(n.product.id), 'name': n.product.name} if n.product else None,
        'po_id': n.po_id,
        'grn_id': n.grn_id,
        'resolved': n.resolved,
        'is_read': user_email in n.read_by,
        'created_at': n.created_at,
    }


class NotificationListView(APIView):
    """
    Alerts visible to the current user's role — Admin/Inventory
    Officer/Warehouse Manager (the "purchase department"). Unresolved
    low-stock alerts and the most recent status notifications, newest first.
    """
    permission_classes = [IsStaff]

    def get(self, request):
        role = request.user.role
        qs = Notification.objects(target_roles=role).order_by('-created_at')[:100]
        items = [_serialize(n, request.user.email) for n in qs]
        unread_count = sum(1 for i in items if not i['is_read'] and not (i['category'] == 'low_stock' and i['resolved']))
        return Response({'results': items, 'unread_count': unread_count})


class NotificationMarkReadView(APIView):
    permission_classes = [IsStaff]

    def post(self, request, notification_id):
        n = Notification.objects(id=notification_id).first()
        if not n:
            return Response({'detail': 'Not found.'}, status=http_status.HTTP_404_NOT_FOUND)
        if request.user.email not in n.read_by:
            n.read_by.append(request.user.email)
            n.save()
        return Response(_serialize(n, request.user.email))


class NotificationMarkAllReadView(APIView):
    permission_classes = [IsStaff]

    def post(self, request):
        role = request.user.role
        email = request.user.email
        for n in Notification.objects(target_roles=role):
            if email not in n.read_by:
                n.read_by.append(email)
                n.save()
        return Response({'detail': 'All notifications marked as read.'})
