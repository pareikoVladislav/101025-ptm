from django.urls import path


from library.views import book_list_view


# api/v1/books/
urlpatterns = [
    path('books/', book_list_view),
]
