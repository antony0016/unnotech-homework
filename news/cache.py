from django.core.cache import cache

# 列表快取 TTL（秒）。作為 invalidation 失敗時的兜底上限；正常情況下
# 爬蟲寫入新資料後會立即 invalidate。
LIST_CACHE_TIMEOUT = 300

# django `cache_page` 產出的實際 key 會帶 prefix + header + path hash，
# 用萬用字元刪除即可一次清掉所有分頁。
LIST_CACHE_WILDCARD = "*news_list*"


def invalidate_list_cache() -> int:
    """清除所有列表頁快取，回傳刪除的 key 數量。

    django-redis 的 `delete_pattern` 支援萬用字元，能一次清掉
    不同 page / page_size 的快取 entry。
    """
    try:
        return cache.delete_pattern(LIST_CACHE_WILDCARD)  # type: ignore[attr-defined]
    except AttributeError:
        # 非 django-redis backend 時退化為清全部快取（測試用 dummy 時會走這裡）
        cache.clear()
        return 0
