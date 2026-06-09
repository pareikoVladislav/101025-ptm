from typing import Any

from rest_framework.generics import get_object_or_404
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.request import Request
from rest_framework import status

from library.serializers import (
    BookListSerializer,
    BookCreateUpdateSerializer,
    BookDetailSerializer,
    BookQueryParamsSerializer
)
from library.models import Book


class BookListCreateAPIView(APIView):

    def filter_queryset(self):
        qs = Book.objects.all()

        query_params = BookQueryParamsSerializer(data=self.request.query_params)
        print(query_params)
        query_params.is_valid(raise_exception=True)
        print(query_params.validated_data)

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
        # books = Book.objects.all()  # -> [Book(1), ..., Book(1000)]
        books = self.filter_queryset()  # -> [Book(1), ..., Book(1000)]
        serializer = BookListSerializer(books, many=True)
        return Response(
            data=serializer.data,  # -> [{'id', 1}, ..., {'id': 1000}]
            status=status.HTTP_200_OK
        )

    def post(self, request: Request, *args, **kwargs) -> Response:
        data = request.data  # {'name': "...", ...}
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
        return get_object_or_404(Book, pk=self.kwargs.get('pk'))

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
