from .base import FamilyConsumerBase


class PantryConsumer(FamilyConsumerBase):
    group_prefix = 'pantry'

    async def connect(self):
        user = self.scope.get('user')
        if not user or not user.is_authenticated:
            await self.close()
            return
        await super().connect()

    async def pantry_updated(self, event):
        """Riceve tutti gli eventi pantry.* e li manda al client."""
        await self.send_json(event['data'])
