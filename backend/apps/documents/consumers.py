import logging
from channels.generic.websocket import AsyncJsonWebsocketConsumer
from channels.db import database_sync_to_async

logger = logging.getLogger(__name__)


class DocumentProgressConsumer(AsyncJsonWebsocketConsumer):
    async def connect(self):
        self.document_id = self.scope["url_route"]["kwargs"]["document_id"]
        self.group_name = f"document_{self.document_id}"

        user = self.scope.get("user")
        if not user or not user.is_authenticated:
            await self.close(code=4001)
            return

        owns = await self._user_owns_document(user, self.document_id)
        if not owns:
            await self.close(code=4003)
            return

        await self.channel_layer.group_add(self.group_name, self.channel_name)
        await self.accept()
        logger.debug("ws_connected", extra={"document_id": self.document_id, "user_id": str(user.id)})

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(self.group_name, self.channel_name)

    async def document_progress(self, event):
        await self.send_json(event["data"])

    @database_sync_to_async
    def _user_owns_document(self, user, document_id: str) -> bool:
        from apps.documents.models import Document
        return Document.objects.filter(id=document_id, user=user).exists()
