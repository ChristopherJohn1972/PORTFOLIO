import secrets
from django.contrib.auth.models import User
from rest_framework.authentication import BaseAuthentication
from rest_framework.exceptions import AuthenticationFailed
from .models import SecurityLog


class TokenAuthentication(BaseAuthentication):
    keyword = 'Bearer'

    def authenticate(self, request):
        auth = request.META.get('HTTP_AUTHORIZATION', '')

        if not auth.startswith(f'{self.keyword} '):
            return None

        token = auth[len(self.keyword) + 1:]

        if not token or len(token) < 10:
            return None

        try:
            from .models import AdminToken
            admin_token = AdminToken.objects.select_related('user').get(token=token)
            user = admin_token.user

            if not user.is_active:
                raise AuthenticationFailed('Account disabled.')

            return (user, token)

        except Exception:
            raise AuthenticationFailed('Invalid or expired token.')


def get_or_create_token(user):
    """Get existing token or create a new one for the user."""
    from .models import AdminToken

    try:
        admin_token = AdminToken.objects.get(user=user)
        return admin_token.token
    except AdminToken.DoesNotExist:
        token = secrets.token_hex(32)
        AdminToken.objects.create(user=user, token=token)
        return token
