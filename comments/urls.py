from django.urls import path
from . import views

urlpatterns = [
    path('add/<int:post_id>/', views.add_comment, name='add_comment'),
    path('<int:comment_id>/reply/', views.reply_comment, name='reply_comment'),
    path('<int:comment_id>/vote/', views.vote_comment, name='vote_comment'),
    path('<int:comment_id>/delete/', views.delete_comment, name='comment_delete'),
    path('<int:comment_id>/report/', views.report_comment, name='report_comment'),
    path('<int:comment_id>/moderate/', views.moderate_comment, name='moderate_comment'),
    path('<int:comment_id>/thread/', views.get_comment_thread, name='comment_thread'),
]