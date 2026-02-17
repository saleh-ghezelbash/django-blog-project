from django.urls import path
from . import views

urlpatterns = [
    path('profile/', views.profile, name='profile'),
    path('change-password/', views.change_password, name='change_password'),

    path('profile/<str:username>/', views.author_profile, name='author_profile'),

    path('follow/<int:author_id>/', views.follow_author, name='follow_author'),
    path('authors/', views.author_list, name='author_list'),
]