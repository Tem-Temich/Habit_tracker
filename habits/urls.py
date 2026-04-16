from rest_framework.routers import DefaultRouter

from .views import HabitViewSet

router = DefaultRouter()
router.register(r"habits", HabitViewSet, basename="habits")

urlpatterns = router.urls

# End of file

# EOF
# EOF2
