import os
from django.core.asgi import get_asgi_application
from channels.routing import ProtocolTypeRouter, URLRouter
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings.development")

django_asgi_app = get_asgi_application()

from apps.documents.routing import websocket_urlpatterns as doc_ws
from apps.chat.routing import websocket_urlpatterns as chat_ws
from services.ws_auth import JwtAuthMiddleware

application = ProtocolTypeRouter(
    {
        "http": django_asgi_app,
        "websocket": JwtAuthMiddleware(
            URLRouter(doc_ws + chat_ws)
        ),
    }
)
