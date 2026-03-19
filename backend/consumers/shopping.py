from .base import FamilyConsumerBase


class ShoppingConsumer(FamilyConsumerBase):
    group_prefix = 'shopping'

    async def connect(self):
        user = self.scope.get('user')
        if not user or not user.is_authenticated:
            await self.close()
            return
        await super().connect()

    async def shopping_updated(self, event):
        """Riceve tutti gli eventi shopping.* e li manda al client."""
        await self.send_json(event['data'])
