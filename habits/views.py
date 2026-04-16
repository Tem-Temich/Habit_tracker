from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.viewsets import ModelViewSet, ReadOnlyModelViewSet

from .models import Habit
from .serializers import HabitSerializer
from .permissions import IsOwner
# Create your views here.

class HabitViewSet(ModelViewSet):
    serializer_class=HabitSerializer
    permission_classes=[IsAuthenticated]

    def get_queryset(self):
        return Habit.objects.