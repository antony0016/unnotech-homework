from rest_framework import serializers

from .models import FocusNews


class FocusNewsListSerializer(serializers.ModelSerializer):
    """列表用 serializer，不含內文以減少傳輸量。"""

    class Meta:
        model = FocusNews
        fields = (
            "id",
            "title",
            "url",
            "image_url",
            "image_caption",
            "author",
            "published_at",
            "created_at",
        )


class FocusNewsDetailSerializer(serializers.ModelSerializer):
    """詳情用 serializer，包含完整內文。"""

    class Meta:
        model = FocusNews
        fields = (
            "id",
            "title",
            "url",
            "image_url",
            "image_caption",
            "content",
            "author",
            "published_at",
            "created_at",
        )
