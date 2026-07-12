from django.contrib import admin
from library.models import Borrow, Book, Author, Library  # Импортируй нужные модели

# Регистрируем модели, чтобы они появились в админке
admin.site.register(Borrow)
admin.site.register(Book)
admin.site.register(Author)
admin.site.register(Library)

