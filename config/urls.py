from django.contrib import admin
from django.urls import include, path

from news.views import news_detail_page, news_list_page

urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/", include("news.urls")),
    path("", news_list_page, name="news-list"),
    path("news/<int:news_id>/", news_detail_page, name="news-detail"),
]
