import logging

from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer
from django.core.management.base import BaseCommand

from news.cache import invalidate_list_cache
from news.consumers import NewsConsumer
from news.scraper import UDNNBAScraper

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    """Management command：抓取 UDN NBA 焦點新聞並寫入 DB。

    供 crontab 定時觸發使用，新抓到的資料會 append 進 FocusNews table，
    已存在的 URL 會被自動略過。有新資料時，透過 Channel Layer 廣播給
    所有連線中的 WebSocket 客戶端。
    """

    help = "Scrape UDN NBA focus news and append to DB"

    def handle(self, *args, **options):
        scraper = UDNNBAScraper()
        created = scraper.scrape_and_save()

        if not created:
            self.stdout.write("No new focus news.")
            return

        self.stdout.write(
            self.style.SUCCESS(f"Created {len(created)} new focus news:")
        )
        for news in created:
            self.stdout.write(f"  [{news.id}] {news.title}")  # type: ignore[attr-defined]

        deleted = invalidate_list_cache()
        self.stdout.write(f"Invalidated {deleted} list cache entries")

        self._broadcast(len(created))

    def _broadcast(self, count: int) -> None:
        """透過 Channel Layer 對 news_updates group 廣播有新聞的事件。"""
        channel_layer = get_channel_layer()
        if channel_layer is None:
            logger.warning("Channel layer is not configured; skip broadcast")
            return
        async_to_sync(channel_layer.group_send)(
            NewsConsumer.GROUP_NAME,
            {"type": "news_created", "count": count},
        )
        self.stdout.write(f"Broadcasted news_created to WebSocket clients (count={count})")
