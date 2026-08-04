"""
ASGI middleware that authenticates WebSocket connections via a JWT access token
passed as the `token` query parameter.

Usage in asgi.py:
    from services.ws_auth import JwtAuthMiddleware
    "websocket": JwtAuthMiddleware(URLRouter(patterns))
"""
from urllib.parse import parse_qs
from channels.db import database_sync_to_async
from django.contrib.auth.models import AnonymousUser


class JwtAuthMiddleware:
    def __init__(self, inner):
        self.inner = inner

    async def __call__(self, scope, receive, send):
        if scope["type"] == "websocket":
            scope["user"] = await self._get_user(scope)
        return await self.inner(scope, receive, send)

    @database_sync_to_async
    def _get_user(self, scope):
        from rest_framework_simplejwt.tokens import AccessToken
        from rest_framework_simplejwt.exceptions import TokenError
        from django.contrib.auth import get_user_model

        User = get_user_model()
        qs = parse_qs(scope.get("query_string", b"").decode())
        token_list = qs.get("token", [])
        if not token_list:
            return AnonymousUser()

        try:
            validated = AccessToken(token_list[0])
            return User.objects.get(id=validated["user_id"])
        except (TokenError, User.DoesNotExist, KeyError):
            return AnonymousUser()
