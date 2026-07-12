from typing import Any

from django.core.exceptions import ValidationError
from django.db.models import Count
from django.utils import timezone
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.authentication import TokenAuthentication
from rest_framework.decorators import action
from rest_framework.filters import SearchFilter, OrderingFilter
from rest_framework.pagination import PageNumberPagination, CursorPagination
from rest_framework.permissions import AllowAny, IsAuthenticated, IsAdminUser, IsAuthenticatedOrReadOnly

from rest_framework.views import APIView
from rest_framework.generics import (
    get_object_or_404,
    GenericAPIView,
    RetrieveUpdateDestroyAPIView,
    ListCreateAPIView,
    ListAPIView
)
from rest_framework.viewsets import ModelViewSet

from rest_framework.response import Response
from rest_framework.request import Request
from rest_framework import status, permissions
from rest_framework_simplejwt.tokens import RefreshToken  # Импорт для работы с JWT
from rest_framework_simplejwt.exceptions import TokenError
from django.contrib.auth import authenticate

from library.serializers import (
    BookListSerializer,
    BookCreateUpdateSerializer,
    BookDetailSerializer,
    BookQueryParamsSerializer,
    CategorySerializer,
    AuthorListSerializer,
    AuthorCreateSerializer,
    UserListSerializer,
    PublisherListSerializer,
    PublisherCreateSerializer,
    PublisherUpdateSerializer,
    PublisherDetailSerializer,
    UserRegisterSerializer  # Наш новый сериализатор регистрации
)
from library.models import Book, Category, Author, User, Publisher
from query_debug import QueryDebug


class CustomPageNumberPaginator(PageNumberPagination):
    page_size = 15
    page_size_query_param = 'page-size'



# ПРЕДСТАВЛЕНИЯ ДЛЯ ДОМАШНЕГО ЗАДАНИЯ 20 (АУТЕНТИФИКАЦИЯ ЧЕРЕЗ HTTP-ONLY COOKIES)


def set_auth_cookies(response, refresh_token):
    """Вспомогательная функция для безопасной упаковки токенов в httpOnly cookies"""
    response.set_cookie(
        key='access_token',
        value=str(refresh_token.access_token),
        httponly=True,
        secure=False,  # Для локальной разработки по HTTP. В продакшене (HTTPS) поставить True
        samesite='Lax',
        max_age=15 * 60  # 15 минут
    )
    response.set_cookie(
        key='refresh_token',
        value=str(refresh_token),
        httponly=True,
        secure=False,
        samesite='Lax',
        max_age=7 * 24 * 60 * 60  # 7 дней
    )


class RegisterAPIView(APIView):
    """Задание 1: Регистрация нового пользователя с валидацией сложности пароля"""
    permission_classes = [permissions.AllowAny]

    def post(self, request: Request) -> Response:
        serializer = UserRegisterSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response({"message": "Пользователь успешно зарегистрирован"}, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class LoginAPIView(APIView):
    """Задание 2: Аутентификация, выдача JWT токенов и их сохранение в httpOnly cookies"""
    permission_classes = [permissions.AllowAny]

    def post(self, request: Request) -> Response:
        username = request.data.get('username')
        password = request.data.get('password')

        # Проверка корректности вводимых данных и существования пользователя
        user = authenticate(username=username, password=password)

        if user is not None:
            refresh = RefreshToken.for_user(user)
            response = Response({
                "message": "Вход выполнен успешно",
                "user": user.username
            }, status=status.HTTP_200_OK)

            # Безопасное сохранение токенов на клиенте в cookies
            set_auth_cookies(response, refresh)
            return response

        return Response({"error": "Неверный логин или пароль"}, status=status.HTTP_401_UNAUTHORIZED)


class CookieTokenRefreshAPIView(APIView):
    """Задание 2: Механизм обновления access токена через refresh токен, извлеченный из кук"""
    permission_classes = [permissions.AllowAny]

    def post(self, request: Request) -> Response:

        refresh_token = request._request.COOKIES.get('refresh_token')

        if not refresh_token:
            return Response({"error": "Refresh token отсутствует в cookies"}, status=status.HTTP_401_UNAUTHORIZED)

        try:
            # 1. Валидируем старый токен из кук
            old_refresh = RefreshToken(refresh_token)

            # 2. Безопасно достаем ID пользователя из его payload
            user_id = old_refresh.payload.get('user_id')
            user = User.objects.get(id=user_id)

            # 3. Генерируем полностью новую пару токенов для пользователя
            new_refresh = RefreshToken.for_user(user)

            # 4. Пытаемся занести старый токен в блэклист (если приложение blacklist установлено)
            try:
                old_refresh.blacklist()
            except AttributeError:
                pass

            response = Response({"message": "Токены успешно обновлены"}, status=status.HTTP_200_OK)

            # 5. Устанавливаем обновленные токены обратно в куки клиента
            set_auth_cookies(response, new_refresh)
            return response

        except (TokenError, User.DoesNotExist):
            return Response({"error": "Невалидный или просроченный токен"}, status=status.HTTP_401_UNAUTHORIZED)


class LogoutAPIView(APIView):
    """Задание 3: Выход из аккаунта. Токены заносятся в Blacklist и удаляются из кук"""
    permission_classes = [permissions.AllowAny]

    def post(self, request: Request) -> Response:
        # ИСПРАВЛЕНО: Используем request._request.COOKIES
        refresh_token = request._request.COOKIES.get('refresh_token')

        if refresh_token:
            try:
                # Помещаем токен в blacklist базы данных
                token = RefreshToken(refresh_token)
                token.blacklist()
            except TokenError:
                pass  # Если токен уже в блэклисте или некорректен, просто игнорируем

        # Удаляем куки с клиента
        response = Response({"message": "Вы успешно вышли из аккаунта"}, status=status.HTTP_200_OK)
        response.delete_cookie('access_token')
        response.delete_cookie('refresh_token')
        return response



# ОРИГИНАЛЬНЫЕ ПРЕДСТАВЛЕНИЯ ИЗ ПРОЕКТА



class MyBooksListView(ListAPIView):
    """Кастомное представление для получения книг текущего пользователя (из ДЗ 19)"""
    serializer_class = BookListSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Book.objects.filter(owner=self.request.user)


class BookListCreateAPIView(APIView):

    def filter_queryset(self):
        qs = Book.objects.all()

        query_params = BookQueryParamsSerializer(data=self.request.query_params)
        query_params.is_valid(raise_exception=True)

        author = query_params.validated_data.get('author')
        sort_by = query_params.validated_data.get('sort_by')
        sort_order = query_params.validated_data.get('sort_order')

        price_gt = query_params.validated_data.get('price_gt')
        price_lt = query_params.validated_data.get('price_lt')

        if author:
            qs = qs.filter(author__surname__icontains=author)

        if price_gt is not None:
            qs = qs.filter(price__gt=price_gt)

        if price_lt is not None:
            qs = qs.filter(price__lt=price_lt)

        if sort_by:
            ordering = sort_by

            if sort_order == "desc":
                ordering = f"-{sort_by}"

            qs = qs.order_by(ordering)

        return qs

    def get(self, request: Request, *args, **kwargs) -> Response:
        books = self.filter_queryset()
        serializer = BookListSerializer(books, many=True)
        return Response(
            data=serializer.data,
            status=status.HTTP_200_OK
        )

    def post(self, request: Request, *args, **kwargs) -> Response:
        data = request.data
        serializer = BookCreateUpdateSerializer(data=data)

        if not serializer.is_valid():
            return Response(
                data=serializer.errors,
                status=status.HTTP_400_BAD_REQUEST
            )

        serializer.save()

        return Response(
            data=serializer.data,
            status=status.HTTP_201_CREATED
        )


class BookRetrieveUpdateDestroyAPIView(APIView):

    def get_object(self):
        return get_object_or_404(
            Book.objects.select_related('category', 'author', 'publisher'),
            pk=self.kwargs.get('pk')
        )

    def update(self, instance: Book, data: dict[str, Any], partial: bool = False):
        serializer = BookCreateUpdateSerializer(
            instance=instance,
            data=data,
            partial=partial
        )

        serializer.is_valid(raise_exception=True)
        serializer.save()

        return Response(
            data=serializer.data,
            status=status.HTTP_200_OK
        )

    def get(self, request: Request, *args, **kwargs) -> Response:
        book = self.get_object()
        serializer = BookDetailSerializer(book)
        return Response(
            data=serializer.data,
            status=status.HTTP_200_OK
        )

    def put(self, request: Request, *args, **kwargs) -> Response:
        book = self.get_object()
        data = request.data

        return self.update(
            book,
            data
        )

    def patch(self, request: Request, *args, **kwargs) -> Response:
        book = self.get_object()
        data = request.data

        return self.update(
            book,
            data,
            partial=True
        )

    def delete(self, request: Request, *args, **kwargs) -> Response:
        book = self.get_object()
        book.delete()
        return Response(
            data={},
            status=status.HTTP_204_NO_CONTENT
        )


class CategoryListCreateGenericAPIView(GenericAPIView):
    queryset = Category.objects.all()
    serializer_class = CategorySerializer
    pagination_class = CustomPageNumberPaginator

    def get(self, request: Request, *args, **kwargs) -> Response:
        categories = self.get_queryset()
        pag = self.paginate_queryset(categories)
        serializer = self.get_serializer(pag, many=True)
        return self.get_paginated_response(serializer.data)

    def post(self, request: Request, *args, **kwargs) -> Response:
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()

        return Response(
            data=serializer.data,
            status=status.HTTP_201_CREATED
        )


class CategoryRetrieveUpdateDestroyGenericView(RetrieveUpdateDestroyAPIView):
    queryset = Category.objects.all()
    serializer_class = CategorySerializer
    lookup_field = 'name'
    lookup_url_kwarg = 'name'


class AuthorListCreateGenericView(ListCreateAPIView):
    pagination_class = CustomPageNumberPaginator

    def get_serializer_class(self):
        if self.request.method == 'GET':
            return AuthorListSerializer
        return AuthorCreateSerializer

    def get_queryset(self):
        qs = Author.objects.all()
        rating_gt = self.request.query_params.get('rating_gt')
        rating_lt = self.request.query_params.get('rating_lt')

        if rating_gt:
            try:
                rating_gt = int(rating_gt)
                qs = qs.filter(rating__gt=rating_gt)
            except ValueError:
                qs = qs.none()

        if rating_lt:
            try:
                rating_lt = int(rating_lt)
                qs = qs.filter(rating__lt=rating_lt)
            except ValueError:
                qs = qs.none()

        return qs

    def create(self, request: Request, *args, **kwargs):
        if 'date_for_birth' not in request.data or not request.data.get('date_for_birth'):
            request.data['date_for_birth'] = timezone.now()

        return super().create(request, *args, **kwargs)


class UserListGenericView(ListAPIView):
    queryset = User.objects.prefetch_related('reviews')
    serializer_class = UserListSerializer

    def get_serializer_context(self):
        context = super().get_serializer_context()
        include_related = self.request.query_params.get('related', 'false')
        context['include_related'] = include_related.lower() == 'true'
        return context

    @QueryDebug(file_name='user-list-query.log')
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)


class CustomCursorPaginator(CursorPagination):
    page_size = 10
    ordering = 'id'


class BookListGenericView(ListAPIView):
    queryset = Book.objects.all()
    serializer_class = BookListSerializer
    pagination_class = CustomCursorPaginator

    filter_backends = [
        DjangoFilterBackend,
        SearchFilter,
        OrderingFilter
    ]

    filterset_fields = [
        'author',
        'price',
        'publisher',
        'category',
        'published_date',
    ]
    search_fields = [
        'name',
        'description',
    ]
    ordering_fields = [
        'id',
        'price',
        'published_date',
    ]


class PublisherViewSet(ModelViewSet):
    queryset = Publisher.objects.all()

    def get_serializer_class(self):
        if self.action == 'list':
            return PublisherListSerializer
        elif self.action == 'create':
            return PublisherCreateSerializer
        elif self.action in {'update', 'partial_update'}:
            return PublisherUpdateSerializer

        return PublisherDetailSerializer

    @action(detail=True, methods=['get'])
    def get_statistic_by_publisher(self, request: Request, *args, **kwargs) -> Response:
        publisher = self.get_object()
        serializer = self.get_serializer(publisher)
        data = serializer.data
        data['count_of_books'] = publisher.books.count()

        return Response(
            data=data,
            status=status.HTTP_200_OK  # <-- ИСПРАВЛЕНО ТУТ
        )

    @action(detail=False, methods=['get'])
    def get_statistic_by_publishers(self, request: Request, *args, **kwargs) -> Response:
        publishers = self.get_queryset()
        publishers = publishers.values('name').annotate(count_of_books=Count('books'))

        return Response(
            data=publishers,
            status=status.HTTP_200_OK
        )


# работа с транзакциями
from django.db import transaction, IntegrityError, DatabaseError


def notify_me():
    print("=" * 100)
    print("Транзакция отработала успешно, отправляю сообщение на email 'test.mail@gmail.com'")
    print("=" * 100)


class AuthorViewSet(ModelViewSet):
    queryset = Author.objects.all()
    serializer_class = AuthorCreateSerializer
    permission_classes = [IsAdminUser]

    @action(detail=False, methods=['post'])
    def create_author_with_books(self, request: Request) -> Response:
        author_data = request.data.get('author')
        books_data = request.data.get('books')

        if not author_data or not isinstance(books_data, list):
            return Response(
                data={'message': 'Запрос должен содержать автора и СПИСОК книг'},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            with transaction.atomic():
                author_serializer = self.get_serializer(data=author_data)
                author_serializer.is_valid(raise_exception=True)
                author = author_serializer.save()

                for book in books_data:
                    book_serializer = BookCreateUpdateSerializer(data=book)
                    book_serializer.is_valid(raise_exception=True)
                    book_serializer.save(author=author)

                transaction.on_commit(notify_me)

        except ValidationError as err:
            return Response(
                data={'error': str(err)},
                status=status.HTTP_400_BAD_REQUEST
            )
        except IntegrityError as err:
            return Response(
                data={'error': f"Нарушение целостности: {str(err)}"},
                status=status.HTTP_400_BAD_REQUEST
            )
        except DatabaseError as err:
            return Response(
                data={'error': f"Ошибка базы данных: {str(err)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

        return Response(
            data={'author': author_serializer.data},
            status=status.HTTP_201_CREATED
        )