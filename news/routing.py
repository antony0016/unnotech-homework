from django.urls import path

from .consumers import NewsConsumer

# Django 的 path/re_path stub 預期接一般 view callable；
# Channels 這裡傳的是 ASGI app（as_asgi），runtime 可用，型別工具會誤報。
websocket_urlpatterns = [
    path("ws/news/", NewsConsumer.as_asgi()),  # type: ignore[arg-type]
]
