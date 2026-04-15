from __future__ import annotations

import logging
import random
import time
from dataclasses import dataclass
from datetime import datetime
from urllib.parse import urlsplit, urlunsplit

import requests
from bs4 import BeautifulSoup
from django.utils.dateparse import parse_datetime

from .models import FocusNews

logger = logging.getLogger(__name__)


@dataclass
class FocusItem:
    """首頁輪播的單一項目（尚未進入詳情頁抓取）。"""

    title: str
    url: str
    image_url: str


class UDNNBAScraper:
    """UDN NBA 焦點新聞爬蟲。

    封裝了從 UDN NBA 首頁抓取輪播新聞、解析詳情頁並寫入 DB 的完整流程。
    設計成類別方便未來換站台時透過繼承覆寫常數或 parser 邏輯。
    """

    INDEX_URL = "https://tw-nba.udn.com/nba/index"
    REQUEST_HEADERS = {
        "User-Agent": (
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
            "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Safari/537.36"
        ),
    }
    REQUEST_TIMEOUT = 15
    # 詳情頁請求之間的隨機延遲區間（秒），用於避免被偵測為自動化爬蟲。
    REQUEST_DELAY_RANGE = (1.0, 3.0)

    def __init__(self, session: requests.Session | None = None) -> None:
        """初始化爬蟲。

        可傳入自訂的 requests.Session（例如測試時注入 mock），
        未傳則自動建立一個，讓多次請求共用連線以提升效率。
        """
        self.session = session or requests.Session()
        self.session.headers.update(self.REQUEST_HEADERS)

    # ------------------------------------------------------------------
    # 內部工具
    # ------------------------------------------------------------------

    def _get_soup_instance(self, url: str) -> BeautifulSoup:
        """發送 GET 請求並回傳解析後的 BeautifulSoup，自帶瀏覽器 UA 和 timeout。"""
        response = self.session.get(url, timeout=self.REQUEST_TIMEOUT)
        response.raise_for_status()
        return BeautifulSoup(response.text, "lxml")

    @staticmethod
    def _correct_url(url: str) -> str:
        """去掉 query string 和 fragment，確保同一篇新聞去重一致。

        UDN 會在連結後面加追蹤參數（例如 `?from=udn_ch2000_menu_v2_main_index`），
        若不處理會繞過 FocusNews.url 的 unique 約束，造成重複入庫。
        """
        parts = urlsplit(str(url))
        return urlunsplit((parts.scheme, parts.netloc, parts.path, "", ""))

    @staticmethod
    def _get_attr(el, name: str) -> str:
        """安全地取出 HTML 屬性值，保證回傳 str。

        處理 BeautifulSoup 的三個情境：元素可能為 None、屬性可能不存在（None）、
        多值屬性（如 class）會回傳 list。全部正規化成去空白的字串，預設為空字串。
        """
        if el is None:
            return ""
        value = el.get(name)
        if value is None:
            return ""
        if isinstance(value, list):
            value = value[0] if value else ""
        return str(value).strip()

    def _sleep_jitter(self) -> None:
        """隨機延遲一段時間，模擬人類瀏覽節奏以降低被反爬偵測的機率。"""
        low, high = self.REQUEST_DELAY_RANGE
        delay = random.uniform(low, high)
        logger.debug("Sleeping %.2fs before next request", delay)
        time.sleep(delay)

    @classmethod
    def _meta(cls, soup: BeautifulSoup, key: str) -> str:
        """依 `property` 或 `name` 取得 `<meta>` 標籤的 content 值。"""
        el = soup.find("meta", attrs={"property": key}) or soup.find(
            "meta", attrs={"name": key}
        )
        return cls._get_attr(el, "content")

    # ------------------------------------------------------------------
    # 對外介面
    # ------------------------------------------------------------------

    def fetch_focus_list(self) -> list[FocusItem]:
        """解析 UDN NBA 首頁，回傳所有輪播焦點新聞項目。

        從每個 `li.splide__slide` 擷取連結、標題、輪播圖片 URL。
        同一頁內以 canonical URL 進行去重。
        """
        soup = self._get_soup_instance(self.INDEX_URL)
        items: list[FocusItem] = []
        seen: set[str] = set()
        for li in soup.select(".splide li.splide__slide"):
            a = li.select_one("a[href]")
            img = li.select_one("picture img, img")
            if not a or not img:
                continue
            href = self._get_attr(a, "href")
            if not href:
                continue
            url = self._correct_url(href)
            if url in seen:
                continue
            seen.add(url)
            title = self._get_attr(a, "title") or a.get_text(strip=True)
            items.append(
                FocusItem(
                    title=title,
                    url=url,
                    image_url=self._get_attr(img, "src"),
                )
            )
        return items

    def fetch_detail(self, url: str) -> dict:
        """抓取詳情頁並擷取標題、內文、圖片說明、作者與發布時間。

        回傳 dict，keys：title、content、image_caption、author、published_at。
        內文為純文字，段落間以兩個換行分隔。
        requests 相關錯誤由呼叫端自行處理。
        """
        soup = self._get_soup_instance(url)
        title_el = soup.select_one("h1")
        title = title_el.get_text(strip=True) if title_el else ""

        body = soup.select_one("#story_body_content")
        if body:
            paragraphs = [
                p.get_text(" ", strip=True)
                for p in body.find_all("p")
                if p.get_text(strip=True)
            ]
            content = "\n\n".join(paragraphs)
        else:
            content = ""

        caption_el = soup.select_one("figure figcaption")
        image_caption = caption_el.get_text(" ", strip=True) if caption_el else ""

        author = self._meta(soup, "dable:author") or self._meta(soup, "author")
        published_raw = self._meta(soup, "article:published_time")
        published_at: datetime | None = (
            parse_datetime(published_raw) if published_raw else None
        )

        return {
            "title": title,
            "content": content,
            "image_caption": image_caption,
            "author": author,
            "published_at": published_at,
        }

    def scrape_and_save(self) -> list[FocusNews]:
        """爬取首頁輪播並抓取每篇新詳情頁，寫入 DB。

        已存在的 URL 會被跳過（以 unique url 去重）。
        單篇詳情頁抓取失敗只會記 log 並跳過，不會中斷整批爬取。
        回傳新增的 FocusNews 清單，方便呼叫端後續廣播（例如透過 WebSocket）。
        """
        created: list[FocusNews] = []
        items = self.fetch_focus_list()
        logger.info("Fetched %d focus items", len(items))

        for index, item in enumerate(items):
            if FocusNews.objects.filter(url=item.url).exists():
                continue
            # 第一篇不等，之後每篇詳情頁請求前都加隨機延遲
            if index > 0:
                self._sleep_jitter()
            try:
                detail = self.fetch_detail(item.url)
            except requests.RequestException as exc:
                logger.warning("Failed to fetch detail %s: %s", item.url, exc)
                continue

            news = FocusNews.objects.create(
                title=detail["title"] or item.title,
                url=item.url,
                image_url=item.image_url,
                image_caption=detail["image_caption"],
                content=detail["content"],
                author=detail["author"],
                published_at=detail["published_at"],
            )
            created.append(news)
            logger.info("Created FocusNews %s: %s", news.id, news.title)  # type: ignore

        return created
