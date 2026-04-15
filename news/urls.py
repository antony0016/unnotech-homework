from rest_framework.routers import DefaultRouter

from .views import FocusNewsViewSet

router = DefaultRouter()
router.register(r"news", FocusNewsViewSet, basename="news")

urlpatterns = router.urls
