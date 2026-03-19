from .base import FamilyConsumerBase


class CalendarConsumer(FamilyConsumerBase):
    group_prefix = 'calendar'

    async def connect(self):
        user = self.scope.get('user')
        if not user or not user.is_authenticated:
            await self.close()
            return
        await super().connect()

    async def calendar_updated(self, event):
        """Riceve tutti gli eventi calendar.* e li manda al client."""
        await self.send_json(event['data'])
