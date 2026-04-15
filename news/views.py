from django.shortcuts import render
from django.utils.decorators import method_decorator
from django.views.decorators.cache import cache_page
from django.views.decorators.vary import vary_on_headers
from rest_framework import viewsets

from .cache import LIST_CACHE_TIMEOUT
from .models import FocusNews
from .pagination import FocusNewsPagination
from .serializers import FocusNewsDetailSerializer, FocusNewsListSerializer


def news_list_page(request):
    """渲染焦點新聞列表頁（HTML 骨架，資料由前端 fetch API 取得）。"""
    return render(request, "news/list.html")


def news_detail_page(request, news_id: int):
    """渲染焦點新聞詳情頁，new_id 會注入給前端 JS 呼叫 API。"""
    return render(request, "news/detail.html", {"news_id": news_id})


class FocusNewsViewSet(viewsets.ReadOnlyModelViewSet):
    """焦點新聞的唯讀 API：列表（list）與詳情（retrieve）。

    列表 endpoint 快取於 Redis（by `?page` / `?page_size` query string），
    爬蟲寫入新資料後會主動 invalidate。
    """

    queryset = FocusNews.objects.all()
    pagination_class = FocusNewsPagination

    def get_serializer_class(self):  # type: ignore[override]
        if self.action == "list":
            return FocusNewsListSerializer
        return FocusNewsDetailSerializer

    @method_decorator(cache_page(LIST_CACHE_TIMEOUT, key_prefix="news_list"))
    @method_decorator(vary_on_headers("Accept"))
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)
