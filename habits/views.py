from rest_framework.decorators import action
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet

from .models import Habit
from .permissions import IsOwner
from .serializers import HabitSerializer


class HabitViewSet(ModelViewSet):
    """
    CRUD-привычек текущего пользователя.
    """

    serializer_class = HabitSerializer
    permission_classes = [IsAuthenticated, IsOwner]

    def get_queryset(self):
        return Habit.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

    @action(detail=False, methods=["get"], permission_classes=[AllowAny])
    def public(self, request, *args, **kwargs):
        """
        Публичный список привычек.

        Для фронта: GET /api/habits/public/
        """
        qs = Habit.objects.filter(is_public=True)
        page = self.paginate_queryset(qs)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        serializer = self.get_serializer(qs, many=True)
        return Response(serializer.data)


# End of file
# EOF
# EOF2
# EOF3