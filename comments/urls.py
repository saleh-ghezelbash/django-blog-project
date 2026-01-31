from django.urls import path
from . import views

urlpatterns = [
    path('<int:pk>/delete/', views.comment_delete, name='comment_delete'),
    path('<int:pk>/toggle/', views.comment_toggle, name='comment_toggle'),
]