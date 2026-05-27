# Django AGGREGATION:


# .aggregate()
# -----------------------------------------------------------------------------
# Метод .aggregate() вызывается на QuerySet (наборе данных).
# Его задача — вычислить агрегатные значения:
# COUNT, AVG, SUM, MIN, MAX и т.д.
#
# ВАЖНО:
# После вызова .aggregate() QuerySet НЕ возвращается.
# Вместо него Django отдаёт обычный Python-словарь.
#
# Пример:
# Book.objects.aggregate(Count('id'))
#
# SQL:
# SELECT COUNT(id) FROM books;
#
# Результат:
# {'id__count': 125}
#
# Используем .aggregate(), когда:
# - нужен один итоговый результат
# - не нужен список объектов
# - нужна статистика по всей таблице
#
# QuerySet:
# [Book(), Book(), Book()]
#
# После aggregate:
# {'books_count': 3}



from django.db.models import Count

# count_of_books = Book.objects.aggregate(
#     books_count=Count('id')
# )['books_count']
#
#
# print(f"Кол-во книг в системе: {count_of_books}")





# .annotate()
# -----------------------------------------------------------------------------
# annotate() работает иначе.
#
# Он НЕ схлопывает QuerySet в один результат,
# а добавляет вычисляемую колонку К КАЖДОМУ объекту.
#
# Было:
# [Book(name, price), Book(name, price)]
#
# После annotate():
# [Book(name, price, reviews_count),
#  Book(name, price, reviews_count)]
#
# SQL:
# SELECT *,
#        COUNT(reviews.id) AS reviews_count
# FROM books;
#
# Используем annotate(), когда:
# - нужна вычисляемая колонка
# - нужно дополнить каждый объект статистикой
# - нужно добавить COUNT/AVG/SUM для каждой записи





# получить список всех авторов + средний рейтинг

from django.db.models import Avg

# authors = Author.objects.annotate(
#     avg_rating=Avg('rating')
# )
#
# print(authors.query)
#
# print(authors)





# annotate() + Count()
# -----------------------------------------------------------------------------
# Здесь мы хотим получить:
# - книги
# - и кол-во отзывов у каждой книги
#
# reviews — related_name из модели Review.
#
# Django автоматически сделает LEFT OUTER JOIN
# и GROUP BY.

# books = Book.objects.annotate(
#     count_of_reviews=Count('reviews')
# )
#
# print(books.query)
#
#
# for book in books:
#     print(book.name, book.count_of_reviews)





# aggregate() + Sum()
# -----------------------------------------------------------------------------
# Получаем сумму цен всех книг.
#
# SQL:
# SELECT SUM(price) FROM books;

# from django.db.models import Sum
#
# price_sum_of_books = Book.objects.aggregate(
#     sum_=Sum('price')
# )
#
# print(price_sum_of_books)





# values() + annotate()
# -----------------------------------------------------------------------------
# values('category')
# превращает QuerySet в группировку по category.
#
# annotate() после values()
# начинает работать как GROUP BY.
#
# SQL:
#
# SELECT category,
#        COUNT(id) AS count_of_books
# FROM books
# GROUP BY category
# ORDER BY count_of_books DESC;

# count_of_books_by_category = Book.objects.values('category').annotate(
#     count_of_books=Count('id')
# ).order_by('-count_of_books')
#
# print(count_of_books_by_category.query)
# print(count_of_books_by_category)





# SQL LIMIT / OFFSET
# -----------------------------------------------------------------------------
# Django slicing на QuerySet автоматически превращается
# в SQL LIMIT и OFFSET.
#
# [10:25]
# =>
# LIMIT 15 OFFSET 10
#
# В БД сначала пропускаются 10 записей,
# потом берутся следующие 15.

# books = Book.objects.all()[10:25]
#
# print(books.query)





# Python slicing
# -----------------------------------------------------------------------------
# Напоминание:
#
# [start:end]
#
# start включительно
# end НЕ включительно

# ['list', 'test', 'one', 'two', 'test'][1:4]
#
# ['test', 'one', 'two']







# SUBQUERY
# =============================================================================
#
# Subquery позволяет встроить один SQL-запрос внутрь другого.
#
# Это буквально:
#
# SELECT ...
# WHERE field IN (
#     SELECT ...
# )
#
# Очень полезно:
# - для сложной фильтрации
# - для вычисляемых колонок
# - для EXISTS
# - для correlated subquery





# Получить книги авторов,
# чей рейтинг >= 7


from django.db.models import Subquery

# subq = Author.objects.filter(
#     rating__gte=7
# ).values('id')
#
#
# main_q = Book.objects.filter(
#     author__in=Subquery(subq)
# )
#
# print(main_q.query)
#
#
# for book in main_q:
#     print(book.id, book.author, book.author.rating)





# OuterRef
# -----------------------------------------------------------------------------
# OuterRef позволяет обратиться к колонке
# из внешнего SQL-запроса.
#
# Это нужно для correlated subquery.
#
# Здесь:
# b2.author_id = b1.author_id
#
# OuterRef('author')
# говорит:
#
# "возьми author из внешнего SELECT"

from django.db.models import Subquery, OuterRef, Min

# sub_query = Book.objects.filter(
#     author=OuterRef('author')
# ).values('author').annotate(
#     min_price=Min('price')
# ).values('min_price')
#
#
# books = Book.objects.filter(
#     published_date__year__gte=2024
# ).annotate(
#     min_author_price=Subquery(sub_query)
# )
#
#
# print(books)





# Что получится:
#
# Название      Цена     Минимальная цена автора
# ------------------------------------------------
# Книга 22      5.7      1.4
#
#
# SQL:
#
# SELECT
#     b1.*,
#     (
#         SELECT MIN(b2.price)
#         FROM books AS b2
#         WHERE b2.author_id = b1.author_id
#     ) AS min_author_price
# FROM books AS b1
# WHERE b1.published_date >= '2024-01-01';





# Decimal problem
# -----------------------------------------------------------------------------
# Python float НЕ предназначен для точных денежных вычислений.
#
# float:
# 0.1 + 0.2 = 0.30000000000000004
#
# Поэтому для денег:
# - Decimal
# - DecimalField
#
# Это особенно важно:
# - цены
# - финансы
# - проценты
# - скидки

# from decimal import Decimal
#
# price = 2.7
# multiple = Decimal('0.3')
#
# print(type(price * multiple))







# ExpressionWrapper
# =============================================================================
#
# F()
# -----------------------------------------------------------------------------
# F() позволяет ссылаться на колонку БД прямо внутри SQL.
#
# Без F():
# Django сначала вытащит данные в Python.
#
# С F():
# вычисление происходит внутри БД.
#
# Это быстрее и эффективнее.
#
#
# ExpressionWrapper
# -----------------------------------------------------------------------------
# Используется, когда Django НЕ может сам определить
# итоговый тип выражения.
#
# Например:
#
# price / pages
#
# Django не всегда понимает:
# это int?
# float?
# decimal?
#
# Поэтому мы явно указываем output_field.



from django.db.models import (
    ExpressionWrapper,
    F,
    DecimalField,
    PositiveSmallIntegerField
)

#
# ExpressionWrapper(
#     expression=...,
#     output_field=...
# )





# Проблемный вариант
# -----------------------------------------------------------------------------
# Django может вернуть неожиданный тип.

# books_price_problem = Book.objects.annotate(
#     price_per_page=(F('price') / F('pages')) * 0.1
# )
#
# print(books_price_problem.query)
# print(books_price_problem)





# Нормальный вариант
# -----------------------------------------------------------------------------
# Мы явно говорим:
#
# "результат должен быть DecimalField"

# books_price_normal = Book.objects.annotate(
#     price_per_page=ExpressionWrapper(
#         expression=(F('price') / F('pages')) * 0.1,
#         output_field=DecimalField(
#             max_digits=6,
#             decimal_places=2
#         )
#     )
# )
#
# print(books_price_normal.query)
# print(books_price_normal)
#
#
# for obj in books_price_normal[:3]:
#     print(obj.price_per_page)
#     print(type(obj.price_per_page))







# SERIALIZERS
# =============================================================================
#
# Serializer в DRF нужен:
#
# 1. Для ВАЛИДАЦИИ входящих данных
# 2. Для ПРЕОБРАЗОВАНИЯ Python -> JSON
# 3. Для ПРЕОБРАЗОВАНИЯ JSON -> Python
#
#
# Serializer работает как:
#
# JSON -> validation -> validated_data
#
#
# Он:
# - проверяет типы
# - проверяет обязательные поля
# - проверяет max_length
# - приводит данные к Python-типам





from rest_framework import serializers
from django.utils import timezone
from datetime import timedelta





# Обычный Serializer
# -----------------------------------------------------------------------------
# Полностью ручное описание полей.

class UserSerializer(serializers.Serializer):
    name = serializers.CharField(max_length=10)
    surname = serializers.CharField(max_length=15)
    age = serializers.IntegerField()
    b_day = serializers.DateField()





# data=
# -----------------------------------------------------------------------------
# data= используется для "сырых" входящих данных.
#
# Обычно:
# - request.data
# - JSON из API
# - данные формы
#
# Serializer начинает процесс валидации.

data = {
    "name": 'vlad',
    "surname": 'test',
    "age": "asdasdasdasdasdasd",
    # "b_day": timezone.now() - timedelta(days=360) * 27
    "b_day": "1999-10-15"
}


user = UserSerializer(data=data)





# is_valid()
# -----------------------------------------------------------------------------
# Запускает:
#
# - проверку типов
# - проверку required
# - max_length
# - кастомные validators
#
# После успешной проверки:
#
# validated_data
#
# станет доступен.

#
# print(user)
#
#
# if user.is_valid():
#     print(user.validated_data)
# else:
#     print(user.errors)





# raise_exception=True
# -----------------------------------------------------------------------------
# Очень часто используется в DRF View/APIView/ViewSet.
#
# Если данные невалидны:
#
# ValidationError
#
# будет выброшен автоматически.

# user.is_valid(raise_exception=True)
#
# print(user.validated_data)









# ModelSerializer
# =============================================================================
#
# ModelSerializer:
#
# - автоматически читает Django-модель
# - сам создаёт serializer fields
# - умеет create()
# - умеет update()
#
# Очень сильно уменьшает boilerplate-код.





# from library.models import Review
#
#
# class ReviewSerializer(serializers.ModelSerializer):
#
#     class Meta:
#         # model =
#         # указываем, какую Django-модель сериализуем
#         model = Review
#
#
#         # fields='__all__'
#         # взять ВСЕ поля модели
#         fields = '__all__'
#
#
#         # fields=['content', 'book']
#         # взять только конкретные поля
#
#
#         # exclude=['rating']
#         # взять всё, кроме rating
#
#
#
# review = Review.objects.get(id=1)
#
#
# print(review)
#
#
# review_data = ReviewSerializer(review)
#
#
# print(review_data)
#
#
# .data
# -----------------------------------------------------------------------------
# Финальное сериализованное представление.
#
# Python object -> dict -> JSON
#
# Обычно именно это уходит в API response.
#
# JsonResponse(serializer.data)

# print(review_data.data)
