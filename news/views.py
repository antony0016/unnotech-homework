from rest_framework import viewsets

from .models import FocusNews
from .pagination import FocusNewsPagination
from .serializers import FocusNewsDetailSerializer, FocusNewsListSerializer


class FocusNewsViewSet(viewsets.ReadOnlyModelViewSet):
    """焦點新聞的唯讀 API：列表（list）與詳情（retrieve）。"""

    queryset = FocusNews.objects.all()
    pagination_class = FocusNewsPagination

    def get_serializer_class(self):  # type: ignore[override]
        if self.action == "list":
            return FocusNewsListSerializer
        return FocusNewsDetailSerializer
