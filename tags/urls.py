from django.urls import path
from . import views

urlpatterns = [
    path('', views.tag_list, name='tag_list'),
    path('<slug:slug>/', views.tag_posts, name='tag_posts'),
]