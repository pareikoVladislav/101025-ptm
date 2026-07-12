from django.urls import path
from rest_framework.routers import SimpleRouter, DefaultRouter
from rest_framework.authtoken.views import obtain_auth_token
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView

from library.views import book_list_create
from library.class_views import (
    BookListCreateAPIView,
    BookRetrieveUpdateDestroyAPIView,
    CategoryListCreateGenericAPIView,
    CategoryRetrieveUpdateDestroyGenericView,
    AuthorListCreateGenericView,
    UserListGenericView,
    BookListGenericView,
    PublisherViewSet,
    AuthorViewSet,
    MyBooksListView,  # Представление из ДЗ 19
    RegisterAPIView,  # ДЗ 20
    LoginAPIView,  # ДЗ 20
    CookieTokenRefreshAPIView,  # ДЗ 20
    LogoutAPIView  # ДЗ 20
)

router = SimpleRouter()
# router = DefaultRouter()
router.register('publishers', PublisherViewSet)
router.register('authors', AuthorViewSet)

# api/v1/
urlpatterns = [

    # ЭНДПОИНТЫ ДЛЯ ДОМАШНЕГО ЗАДАНИЯ 20 (АУТЕНТИФИКАЦИЯ ЧЕРЕЗ HTTP-ONLY COOKIES)

    path('auth/register/', RegisterAPIView.as_view(), name='auth-register'),
    path('auth/login/', LoginAPIView.as_view(), name='auth-login'),
    path('auth/refresh/', CookieTokenRefreshAPIView.as_view(), name='auth-refresh'),
    path('auth/logout/', LogoutAPIView.as_view(), name='auth-logout'),

    # СТАНДАРТНЫЕ МАРШРУТЫ АУТЕНТИФИКАЦИИ (ДЛЯ СРАВНЕНИЯ)

    path('api-token-auth/', obtain_auth_token),
    path('jwt-auth/', TokenObtainPairView.as_view()),
    path('jwt-refresh/', TokenRefreshView.as_view()),

    # ОСНОВНЫЕ МАРШРУТЫ ПРИЛОЖЕНИЯ

    # Эндпоинт для получения книг текущего авторизованного пользователя (из ДЗ 19)
    path('books/my/', MyBooksListView.as_view(), name='my-books'),

    # ИСПРАВЛЕНО: Теперь этот путь использует класс, который поддерживает и GET, и POST!
    path('books/', BookListCreateAPIView.as_view()),

    path('books/<int:pk>/', BookRetrieveUpdateDestroyAPIView.as_view()),
    path('categories/', CategoryListCreateGenericAPIView.as_view()),
    path('categories/<str:name>/', CategoryRetrieveUpdateDestroyGenericView.as_view()),
    # path('authors/', AuthorListCreateGenericView.as_view()),
    path('users/', UserListGenericView.as_view()),
]

# Подключение маршрутов ViewSets (publishers, authors)
urlpatterns += router.urls