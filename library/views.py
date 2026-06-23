from rest_framework.decorators import api_view
from rest_framework.generics import get_object_or_404
from rest_framework.response import Response
from rest_framework.request import Request
from rest_framework import status

from library.serializers import BookListSerializer, BookCreateUpdateSerializer
from library.models import Book


@api_view(['GET',])
def book_list_view(request):
    books = Book.objects.all()
    serializer = BookListSerializer(books, many=True)
    return Response(
        data=serializer.data,
        status=200
    )


@api_view(['GET', 'POST',])
def book_list_create(request: Request):
    if request.method == "GET":
        books = Book.objects.all()
        serializer = BookListSerializer(books, many=True)
        return Response(
            data=serializer.data,
            status=status.HTTP_200_OK
        )

    if request.method == "POST":
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


@api_view(['PUT',])
def book_update(request: Request, pk: int):
    try:
        book = Book.objects.get(pk=pk)
    except Book.DoesNotExist as err:
        return Response(
            data=str(err),
            status=status.HTTP_404_NOT_FOUND
        )

    data = request.data
    serializer = BookCreateUpdateSerializer(instance=book, data=data)

    if not serializer.is_valid():
        return Response(
            data=serializer.errors,
            status=status.HTTP_400_BAD_REQUEST
        )

    serializer.save()

    return Response(
        data=serializer.data,
        status=status.HTTP_200_OK
    )


@api_view(['DELETE',])
def book_delete(request: Request, pk: int):
    try:
        book = Book.objects.get(pk=pk)
    except Book.DoesNotExist as err:
        return Response(
            data=str(err),
            status=status.HTTP_404_NOT_FOUND
        )

    book.delete()
    return Response(status=status.HTTP_204_NO_CONTENT)