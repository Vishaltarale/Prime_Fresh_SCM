from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework_simplejwt.exceptions import AuthenticationFailed
from mongoengine.errors import DoesNotExist, ValidationError as MongoValidationError

from .models import User


class MongoJWTAuthentication(JWTAuthentication):
    """
    simplejwt's default get_user() looks up the Django ORM AUTH_USER_MODEL.
    This project's users live in MongoEngine, so we override user lookup only;
    token encode/decode/validation (the actual JWT mechanics) are unchanged.
    """

    def get_user(self, validated_token):
        user_id = validated_token.get('user_id')
        if user_id is None:
            raise AuthenticationFailed('Token contained no recognizable user identification')
        try:
            return User.objects.get(id=user_id)
        except (DoesNotExist, MongoValidationError):
            raise AuthenticationFailed('User not found', code='user_not_found')
