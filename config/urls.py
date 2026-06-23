from django.contrib import admin
from django.urls import path, include
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from test_app.views import greetings

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api-auth/', include('rest_framework.urls')),
    path('home-page/', greetings),
    path('api/v1/', include('library.urls')),

    # Эндпоинты для работы с JWT-токенами (Задание 1)
    path('api/v1/jwt-auth/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('api/v1/jwt-auth/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
]