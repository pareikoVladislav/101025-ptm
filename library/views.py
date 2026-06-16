from rest_framework.viewsets import ModelViewSet
from rest_framework.decorators import action
from rest_framework.response import Response
from library.models import Category
from library.serializers import CategorySerializer


class CategoryViewSet(ModelViewSet):
    """
    ModelViewSet для полной CRUD-реализации Категорий.
    Автоматически обрабатывает создание, чтение, обновление и мягкое удаление.
    """
    queryset = Category.objects.all()
    serializer_class = CategorySerializer

    # Кастомный метод подсчета связанных книг/задач (Задание 1)
    # Будет доступен по урлу: GET /api/categories/{id}/count_tasks/
    @action(detail=True, methods=['get'], url_path='count_tasks')
    def count_tasks(self, request, pk=None):
        category = self.get_object()
        # Считаем книги, привязанные к текущей категории
        books_count = category.books.count()

        return Response({
            'category_id': category.id,
            'category_name': category.name,
            'tasks_count': books_count  # Ключ назван строго по ТЗ
        })