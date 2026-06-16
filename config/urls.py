from django.contrib import admin
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from library.views import CategoryViewSet

# Настраиваем автоматические маршруты DRF для нашего ViewSet
router = DefaultRouter()
router.register(r'categories', CategoryViewSet, basename='category')

urlpatterns = [
    path('admin/', admin.site.urls),
    
    # Эндпоинты категорий от роутера (Задание 1)
    path('api/', include(router.urls)),
]