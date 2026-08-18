from mongoengine.errors import ValidationError as MongoValidationError
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated

from .permissions import get_linked_entity
from .serializers import UserSerializer

# Which entity fields each external role may edit about themselves, and how
# they map onto the User login fields that mirror them (full_name/phone stay
# in sync on both records so they don't drift apart).
ENTITY_EDITABLE_FIELDS = {
    'Customer': ['phone', 'address', 'city', 'state'],
    'Supplier': ['phone', 'company_name', 'address', 'state', 'district'],
    'Farmer': ['phone', 'address', 'village', 'district', 'state'],
}


def _serialize_entity(entity, role):
    if not entity:
        return None
    data = {'id': str(entity.id)}
    for field in ENTITY_EDITABLE_FIELDS.get(role, []):
        data[field] = getattr(entity, field, '') or ''
    return data


class MyProfileView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user
        entity = get_linked_entity(user)
        return Response({
            'user': UserSerializer(user).data,
            'entity': _serialize_entity(entity, user.role),
        })

    def put(self, request):
        user = request.user
        data = request.data

        if 'full_name' in data:
            user.full_name = data['full_name']
        if 'phone' in data:
            user.phone = data['phone']
        user.save()

        entity = get_linked_entity(user)
        if entity:
            editable = ENTITY_EDITABLE_FIELDS.get(user.role, [])
            for field in editable:
                if field in data:
                    setattr(entity, field, data[field])
            # Keep the entity's name/contact fields in sync with the login.
            if user.role == 'Customer':
                entity.full_name = user.full_name
            elif user.role == 'Supplier':
                entity.supplier_name = user.full_name
            elif user.role == 'Farmer':
                entity.full_name = user.full_name
            try:
                entity.save()
            except MongoValidationError as exc:
                return Response({'detail': str(exc)}, status=400)

        return Response({
            'user': UserSerializer(user).data,
            'entity': _serialize_entity(entity, user.role),
        })
