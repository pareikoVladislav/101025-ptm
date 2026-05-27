from rest_framework import serializers

from library.models import Book


# Сериализатор называем, как <ModelName>+<action>+Serializer
class BookListSerializer(serializers.ModelSerializer):
    """
    Модел сериалайзер умеет привязываться к конкретной указаной модели.
    Когда мы указываем ему мета класс, там мы говорим:
    1. На какую модель должен привязаться сериалайзер
    2. В этой модели, на какие поля он должен смотреть (fields), или
    какие поля он должен исключить (exclude)
    """
    class Meta:
        model = Book
        fields = [
            'id',
            'name',
            'author',
            'price',
            'category',
        ]
