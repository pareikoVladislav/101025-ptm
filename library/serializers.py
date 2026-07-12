from typing import Any
from rest_framework import serializers
from django.contrib.auth.password_validation import validate_password  # Для валидации сложности пароля

from library.models import Book, Library, Category, Author, User, Review, Publisher


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
        sort_by = attrs.get("sort_by")
        sort_order = attrs.get("sort_order")

        if price_gt is not None and price_lt is not None and price_gt >= price_lt:
            raise serializers.ValidationError(
                {
                    "price_gt": "price_gt must be less than price_lt.",
                    "price_lt": "price_lt must be greater than price_gt.",
                }
            )

        if sort_order and not sort_by:
            raise serializers.ValidationError(
                {
                    "sort_order": "sort_order can be used only together with sort_by."
                }
            )

        return attrs


class LibraryShortInfoSerializer(serializers.ModelSerializer):

    class Meta:
        model = Library
        fields = [
            'id',
            'name'
        ]


class BookDetailSerializer(serializers.ModelSerializer):
    author = serializers.StringRelatedField()
    libraries = LibraryShortInfoSerializer(
        many=True,
        read_only=True
    )
    publisher = serializers.StringRelatedField()
    category = serializers.SlugRelatedField(
        slug_field='name',
        read_only=True
    )

    class Meta:
        model = Book
        exclude = [
            'owner',
            'published_date',
        ]


class BookListSerializer(serializers.ModelSerializer):
    class Meta:
        model = Book
        fields = [
            'id',
            'name',
            'author',
            'price',
            'category',
        ]


class BookCreateUpdateSerializer(serializers.ModelSerializer):
    price = serializers.DecimalField(
        max_digits=6,
        decimal_places=2,
    )

    discount_percentage = serializers.IntegerField(
        min_value=0,
        max_value=100,
        write_only=True,
        required=False
    )

    class Meta:
        model = Book
        fields = [
            'name',
            'author',
            'libraries',
            'price',
            'discount_percentage',
            'category',
        ]

    def create(self, validated_data: dict) -> Book:
        discount_percentage = validated_data.pop('discount_percentage', None)
        libraries = validated_data.pop('libraries', [])

        book = Book.objects.create(**validated_data)

        if discount_percentage is not None:
            book.discounted_price = book.price * (1 - discount_percentage / 100)
            book.save(update_fields=['discounted_price'])

        if libraries:
            book.libraries.set(libraries)

        return book

    def update(self, instance: Book, validated_data: dict) -> Book:
        discount_percentage = validated_data.pop('discount_percentage', None)
        libraries = validated_data.pop('libraries', None)

        for attr, value in validated_data.items():
            setattr(instance, attr, value)

        if discount_percentage is not None:
            instance.discounted_price = instance.price * (1 - discount_percentage / 100)

        instance.save()

        if libraries is not None:
            instance.libraries.set(libraries)

        return instance


class CategorySerializer(serializers.ModelSerializer):

    class Meta:
        model = Category
        fields = '__all__'
        read_only_fields = ['deleted_at']


class AuthorListSerializer(serializers.ModelSerializer):

    class Meta:
        model = Author
        fields = [
            'id',
            'surname',
            'rating'
        ]


class AuthorCreateSerializer(serializers.ModelSerializer):

    class Meta:
        model = Author
        fields = [
            'name',
            'surname',
            'date_for_birth',
            'rating',
        ]


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



# СЕРИАЛИЗАТОРЫ ДЛЯ ДОМАШНЕГО ЗАДАНИЯ 20 (АУТЕНТИФИКАЦИЯ)


class UserRegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(
        write_only=True,
        required=True,
        validators=[validate_password]  # Валидация минимальных требований к сложности пароля Django
    )
    email = serializers.EmailField(required=True)

    class Meta:
        model = User
        fields = ['username', 'email', 'password', 'first_name', 'last_name']

    def validate_email(self, value):
        # Обязательная проверка уникальности email в системе
        if User.objects.filter(email=value).exists():
            raise serializers.ValidationError("Пользователь с таким email уже существует.")
        return value

    def create(self, validated_data):
        # Хэширование и сохранение пароля в БД через create_user
        user = User.objects.create_user(
            username=validated_data['username'],
            email=validated_data['email'],
            password=validated_data['password'],
            first_name=validated_data.get('first_name', ''),
            last_name=validated_data.get('last_name', '')
        )
        return user



# ИЗНАЧАЛЬНЫЕ СЕРИАЛИЗАТОРЫ ИЗДАТЕЛЕЙ


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


class PublisherUpdateSerializer(serializers.ModelSerializer):

    class Meta:
        model = Publisher
        fields = '__all__'