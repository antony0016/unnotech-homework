import logging

from django.core.management.base import BaseCommand

from news.scraper import UDNNBAScraper

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    """Management command：抓取 UDN NBA 焦點新聞並寫入 DB。

    供 crontab 定時觸發使用，新抓到的資料會 append 進 FocusNews table，
    已存在的 URL 會被自動略過。
    """

    help = "Scrape UDN NBA focus news and append to DB"

    def handle(self, *args, **options):
        scraper = UDNNBAScraper()
        created = scraper.scrape_and_save()

        if created:
            self.stdout.write(
                self.style.SUCCESS(f"Created {len(created)} new focus news:")
            )
            for news in created:
                self.stdout.write(f"  [{news.id}] {news.title}")  # type: ignore[attr-defined]
        else:
            self.stdout.write("No new focus news.")
