from django.urls import path

from accounts.views import MyTokenObtainPairView

urlpatterns = [
    path("api/token/", MyTokenObtainPairView.as_view()),
]