from django.urls import path
from . import views

urlpatterns = [
    path('', views.library_home, name='library_home'),
    path('book/<int:book_id>/', views.book_detail, name='book_detail'),
    path('view-book/<int:book_id>/', views.view_book, name='view_book'),
    path('save-book/', views.save_book, name='save_book'),
    path('buy-book/', views.buy_book, name='buy_book'),
    path('check-payment/', views.check_payment, name='check_payment'),  # Thêm endpoint mới
    path('saved-books/', views.saved_books, name='saved_books'),
    path('remove-saved-book/<int:book_id>/', views.remove_saved_book, name='remove_saved_book'),
    path('add-book/', views.add_book, name='add_book'),
    path('webhook/sepay/', views.sepay_webhook, name='sepay_webhook'),
    path('delete-book/<int:book_id>/', views.delete_book, name='delete_book'),
]
