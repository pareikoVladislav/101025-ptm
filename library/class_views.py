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
from rest_framework import status

from library.serializers import (
    BookListSerializer,
    BookCreateUpdateSerializer,
    BookDetailSerializer,
    BookQueryParamsSerializer,
    CategorySerializer,
    # AuthorSerializer,
    AuthorListSerializer,
    AuthorCreateSerializer,
    UserListSerializer, PublisherListSerializer, PublisherCreateSerializer,
    PublisherUpdateSerializer, PublisherDetailSerializer
)
from library.models import Book, Category, Author, User, Publisher
from query_debug import QueryDebug


class CustomPageNumberPaginator(PageNumberPagination):
    page_size = 6


class CustomCursorPaginator(CursorPagination):
    page_size = 3
    ordering = 'id'


class BookListCreateAPIView(APIView):
    # Задание 2: Мутации данных доступны только авторизованным по JWT пользователям
    permission_classes = [IsAuthenticatedOrReadOnly]

    def filter_queryset(self):
        qs = Book.objects.all().order_by('id')

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
    # Задание 2: Изменение конкретной книги разрешено только авторизованным пользователям
    permission_classes = [IsAuthenticatedOrReadOnly]

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
        return self.update(book, data)

    def patch(self, request: Request, *args, **kwargs) -> Response:
        book = self.get_object()
        data = request.data
        return self.update(book, data, partial=True)

    def delete(self, request: Request, *args, **kwargs) -> Response:
        book = self.get_object()
        book.delete()
        return Response(
            data={},
            status=status.HTTP_204_NO_CONTENT
        )


class CategoryListCreateGenericAPIView(GenericAPIView):
    queryset = Category.objects.all().order_by('id')
    serializer_class = CategorySerializer
    # Задание 2: Чтение доступно всем, создание категорий — по токену
    permission_classes = [IsAuthenticatedOrReadOnly]

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
    permission_classes = [IsAuthenticatedOrReadOnly]


class AuthorListCreateGenericView(ListCreateAPIView):
    permission_classes = [IsAuthenticatedOrReadOnly]

    def get_serializer_class(self):
        if self.request.method == 'GET':
            return AuthorListSerializer
        return AuthorCreateSerializer

    def get_queryset(self):
        qs = Author.objects.all().order_by('id')
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
    queryset = User.objects.prefetch_related('reviews').order_by('id')
    serializer_class = UserListSerializer
    # Задание 2: Просмотр списка пользователей строго ограничен администраторами
    permission_classes = [IsAdminUser]

    def get_serializer_context(self):
        context = super().get_serializer_context()
        include_related = self.request.query_params.get('related', 'false')
        context['include_related'] = include_related.lower() == 'true'
        return context

    @QueryDebug(file_name='user-list-query.log')
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)


class BookListGenericView(ListAPIView):
    queryset = Book.objects.all().order_by('id')
    serializer_class = BookListSerializer
    # Задание 2: Просматривать каталог книг могут абсолютно все (включая неавторизованных)
    permission_classes = [AllowAny]

    # Задание 3: Мы закомментировали локальный пагинатор CustomPageNumberPaginator.
    # Теперь этот эндпоинт автоматически применит ГЛОБАЛЬНУЮ пагинацию на 5 элементов из settings.py.
    # pagination_class = CustomPageNumberPaginator

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
    queryset = Publisher.objects.all().order_by('id')
    permission_classes = [IsAuthenticatedOrReadOnly]

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
        return Response(data=data, status=status.HTTP_200_OK)

    @action(detail=False, methods=['get'])
    def get_statistic_by_publishers(self, request: Request, *args, **kwargs) -> Response:
        publishers = self.get_queryset()
        publishers = publishers.values('name').annotate(count_of_books=Count('books'))
        return Response(data=publishers, status=status.HTTP_200_OK)


from django.db import transaction, IntegrityError, DatabaseError


def notify_me():
    print("=" * 100)
    print("Транзакция отработала успешно, отправляю сообщение на email 'test.mail@gmail.com'")
    print("=" * 100)


class AuthorViewSet(ModelViewSet):
    queryset = Author.objects.all().order_by('id')
    serializer_class = AuthorCreateSerializer
    # Задание 2: Действия с авторами доступны только администраторам системы
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
                # step 1 создание автора
                author_serializer = self.get_serializer(data=author_data)
                author_serializer.is_valid(raise_exception=True)
                author = author_serializer.save()

                # step 2 создание книжек для этого автора
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