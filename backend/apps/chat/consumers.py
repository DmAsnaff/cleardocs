import logging
from channels.generic.websocket import AsyncJsonWebsocketConsumer
from channels.db import database_sync_to_async

logger = logging.getLogger(__name__)


class ChatConsumer(AsyncJsonWebsocketConsumer):
    async def connect(self):
        self.session_id = self.scope["url_route"]["kwargs"]["session_id"]
        self.group_name = f"chat_{self.session_id}"

        user = self.scope.get("user")
        if not user or not user.is_authenticated:
            await self.close(code=4001)
            return

        owns = await self._user_owns_session(user, self.session_id)
        if not owns:
            await self.close(code=4003)
            return

        await self.channel_layer.group_add(self.group_name, self.channel_name)
        await self.accept()
        logger.debug("chat_ws_connected", extra={"session_id": self.session_id})

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(self.group_name, self.channel_name)

    async def receive_json(self, content):
        # All user input goes via REST — this WS is receive-only for streaming
        pass

    async def chat_message(self, event):
        """Forward chat events (token, stream_start, stream_end, error) to the browser."""
        await self.send_json(event["data"])

    @database_sync_to_async
    def _user_owns_session(self, user, session_id: str) -> bool:
        from apps.chat.models import ChatSession
        return ChatSession.objects.filter(id=session_id, user=user).exists()
