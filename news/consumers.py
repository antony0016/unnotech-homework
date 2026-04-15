import json

from channels.generic.websocket import AsyncWebsocketConsumer


class NewsConsumer(AsyncWebsocketConsumer):
    """推播焦點新聞更新事件給訂閱的前端。

    前端連上 `/ws/news/` 後會被加入 `news_updates` group；
    當爬蟲抓到新資料時，scrape_news command 會對該 group 廣播，
    前端收到訊息後即可重新 fetch 列表。
    """

    GROUP_NAME = "news_updates"

    async def connect(self):
        await self.channel_layer.group_add(self.GROUP_NAME, self.channel_name)
        await self.accept()

    async def disconnect(self, code):
        await self.channel_layer.group_discard(self.GROUP_NAME, self.channel_name)

    async def news_created(self, event):
        """Channel Layer group_send 過來的事件 handler。"""
        await self.send(
            text_data=json.dumps(
                {"type": "news_created", "count": event.get("count", 0)}
            )
        )
