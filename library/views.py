from rest_framework.decorators import api_view
from rest_framework.response import Response

from library.serializers import BookListSerializer
from library.models import Book


@api_view(['GET',])
def book_list_view(request):
    # 1. Получить набор данных
    books = Book.objects.all()

    # 2. Данные -- сложные объекты, нужно упростить
    # первый параметр -- это instance, то есть то, что мы хотим преобразить.
    # по умолчанию ВСЕ сериазизаторы работают с настройкой только на один объект.
    # если мы передаём много объектов (список), то сериализатору нужно помочь, добавив параметр
    # many=True. Так сериализатор поймёт, что пришшло много объектов и не будет пытаться
    # получить у списка через точку, допустим, name книги. Ведь теперь он знает, что перед ним не
    # один объект, а N объектов в списке.
    serializer = BookListSerializer(books, many=True)

    # 3. Вернуть ответет
    return Response(
        data=serializer.data,
        status=200 # пока что статусы возвращаем явно в виде циферок. Потом сделаем красивее
        # и будем использовать специальные константы
    )
