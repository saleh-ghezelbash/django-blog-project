from django.urls import path
from . import views

urlpatterns = [
    path('', views.contact_us, name='contact_us'),
    path('submit/', views.contact_submit, name='contact_submit'),
    path('success/', views.contact_success, name='contact_success'),
]