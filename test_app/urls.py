from django.urls import path


from library.views import book_list_view, book_list_create, book_read_update_delete


# api/v1/books/
urlpatterns = [
    # path('books/', book_list_view),

    # CRUD - 4
    path('books/', book_list_create), # read all, create
    path('books/<int:pk>/', book_read_update_delete), # read id, update id, delete id
]
