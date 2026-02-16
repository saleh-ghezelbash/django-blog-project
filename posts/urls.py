from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('posts/', views.post_list, name='post_list'),
    path('posts/create/', views.post_create, name='post_create'),
    path('posts/<int:pk>/update/', views.post_update, name='post_update'),
    path('posts/<int:pk>/delete/', views.post_delete, name='post_delete'),
    path('posts/<int:year>/<int:month>/<int:day>/<slug:slug>/', 
         views.post_detail, name='post_detail'),
    path('search/', views.search, name='search'),
    path('search/advanced/', views.advanced_search, name='advanced_search'),
]