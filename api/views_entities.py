from mongoengine.errors import NotUniqueError, ValidationError as MongoValidationError
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status as http_status
from rest_framework.pagination import PageNumberPagination

from .entities import ENTITY_REGISTRY, serialize_instance, validate_and_coerce
from .permissions import IsAdmin


class EntityPagination(PageNumberPagination):
    page_size = 10
    page_size_query_param = 'page_size'
    max_page_size = 100


def _get_registry_entry(entity):
    return ENTITY_REGISTRY.get(entity)


class EntityMetaView(APIView):
    """Field schema for a given entity — drives the generic React list+form UI."""
    permission_classes = [IsAdmin]

    def get(self, request, entity):
        entry = _get_registry_entry(entity)
        if not entry:
            return Response({'detail': f'Unknown entity "{entity}".'}, status=http_status.HTTP_404_NOT_FOUND)
        return Response({'entity': entity, 'label': entry['label'], 'fields': entry['fields']})


class EntityListCreateView(APIView):
    permission_classes = [IsAdmin]

    def get(self, request, entity):
        entry = _get_registry_entry(entity)
        if not entry:
            return Response({'detail': f'Unknown entity "{entity}".'}, status=http_status.HTTP_404_NOT_FOUND)

        model = entry['model']
        search = request.query_params.get('search', '').strip()
        qs = model.objects.all()
        if search:
            from mongoengine.queryset.visitor import Q
            query = Q()
            for field_name in entry['search_fields']:
                query |= Q(**{f'{field_name}__icontains': search})
            qs = qs.filter(query)

        records = list(qs)
        paginator = EntityPagination()
        page = paginator.paginate_queryset(records, request)
        data = [serialize_instance(instance, entry['fields']) for instance in page]
        return paginator.get_paginated_response(data)

    def post(self, request, entity):
        entry = _get_registry_entry(entity)
        if not entry:
            return Response({'detail': f'Unknown entity "{entity}".'}, status=http_status.HTTP_404_NOT_FOUND)

        cleaned, errors = validate_and_coerce(request.data, entry['fields'])
        if errors:
            return Response(errors, status=http_status.HTTP_400_BAD_REQUEST)

        try:
            instance = entry['model'](**cleaned)
            instance.save()
        except NotUniqueError:
            return Response({'detail': 'A record with these unique fields already exists.'}, status=http_status.HTTP_400_BAD_REQUEST)
        except MongoValidationError as exc:
            return Response({'detail': str(exc)}, status=http_status.HTTP_400_BAD_REQUEST)

        return Response(serialize_instance(instance, entry['fields']), status=http_status.HTTP_201_CREATED)


class EntityDetailView(APIView):
    permission_classes = [IsAdmin]

    def _get_instance(self, entry, object_id):
        try:
            return entry['model'].objects(id=object_id).first()
        except MongoValidationError:
            return None

    def get(self, request, entity, object_id):
        entry = _get_registry_entry(entity)
        if not entry:
            return Response({'detail': f'Unknown entity "{entity}".'}, status=http_status.HTTP_404_NOT_FOUND)
        instance = self._get_instance(entry, object_id)
        if not instance:
            return Response({'detail': 'Not found.'}, status=http_status.HTTP_404_NOT_FOUND)
        return Response(serialize_instance(instance, entry['fields']))

    def put(self, request, entity, object_id):
        entry = _get_registry_entry(entity)
        if not entry:
            return Response({'detail': f'Unknown entity "{entity}".'}, status=http_status.HTTP_404_NOT_FOUND)
        instance = self._get_instance(entry, object_id)
        if not instance:
            return Response({'detail': 'Not found.'}, status=http_status.HTTP_404_NOT_FOUND)

        cleaned, errors = validate_and_coerce(request.data, entry['fields'], partial=True)
        if errors:
            return Response(errors, status=http_status.HTTP_400_BAD_REQUEST)

        try:
            for key, value in cleaned.items():
                setattr(instance, key, value)
            instance.save()
        except NotUniqueError:
            return Response({'detail': 'A record with these unique fields already exists.'}, status=http_status.HTTP_400_BAD_REQUEST)
        except MongoValidationError as exc:
            return Response({'detail': str(exc)}, status=http_status.HTTP_400_BAD_REQUEST)

        return Response(serialize_instance(instance, entry['fields']))

    def delete(self, request, entity, object_id):
        entry = _get_registry_entry(entity)
        if not entry:
            return Response({'detail': f'Unknown entity "{entity}".'}, status=http_status.HTTP_404_NOT_FOUND)
        instance = self._get_instance(entry, object_id)
        if not instance:
            return Response({'detail': 'Not found.'}, status=http_status.HTTP_404_NOT_FOUND)
        instance.delete()
        return Response(status=http_status.HTTP_204_NO_CONTENT)
