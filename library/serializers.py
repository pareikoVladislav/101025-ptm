from typing import Any
from rest_framework import serializers
from library.models import Book, Library, Category, Author, User, Review, Publisher

# Сериализатор для Категорий (Задание 1 и 2)
class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = ['id', 'name', 'is_deleted', 'deleted_at']
        read_only_fields = ['is_deleted', 'deleted_at']


class BookQueryParamsSerializer(serializers.Serializer):
    author = serializers.CharField(required=False)
    price_gt = serializers.DecimalField(
        required=False,
        max_digits=10,
        decimal_places=2,
        min_value=0,
    )
    price_lt = serializers.DecimalField(
        required=False,
        max_digits=10,
        decimal_places=2,
        min_value=0,
    )
    sort_by = serializers.ChoiceField(
        required=False,
        choices=("title", "author", "price", "published_date"),
    )
    sort_order = serializers.ChoiceField(
        required=False,
        choices=("asc", "desc"),
    )

    def validate_author(self, value: str) -> str:
        value = value.strip()

        if not value.replace("-", "").replace(" ", "").isalpha():
            raise serializers.ValidationError(
                "Author's last name must contain only alphabetic symbols, spaces or hyphens."
            )

        return value

    def validate(self, attrs: dict[str, Any]) -> dict[str, Any]:
        price_gt = attrs.get("price_gt")
        price_lt = attrs.get("price_lt")
        return attrs


class UserListSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = [
            'id',
            'username',
            'role',
            'gender',
        ]

    def to_representation(self, instance):
        data = super().to_representation(instance)
        if self.context.get('include_related'):
            data['reviews'] = [
                {
                    'id': review.id,
                    'content': review.content,
                    'rating': review.rating,
                }
                for review in instance.reviews.all()
            ]
        return data


class PublisherListSerializer(serializers.ModelSerializer):
    class Meta:
        model = Publisher
        fields = [
            'id',
            'name'
        ]


class PublisherDetailSerializer(serializers.ModelSerializer):
    count_of_books = serializers.IntegerField(
        required=False
    )

    class Meta:
        model = Publisher
        fields = '__all__'


class PublisherCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Publisher
        fields = [
            'name',
            'address',
            'country',
        ]