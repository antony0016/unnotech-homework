from rest_framework.pagination import PageNumberPagination


class FocusNewsPagination(PageNumberPagination):
    """焦點新聞分頁，預設每頁 5 筆，可透過 `?page_size=` 覆寫（上限 20）。"""

    page_size = 5
    page_size_query_param = "page_size"
    max_page_size = 20
