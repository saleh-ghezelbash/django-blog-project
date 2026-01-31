from django.contrib import admin
from .models import Comment

@admin.register(Comment)
class CommentAdmin(admin.ModelAdmin):
    list_display = ['post', 'author', 'name', 'email', 'created_at', 'active']
    list_filter = ['active', 'created_at', 'post']
    search_fields = ['name', 'email', 'content']
    actions = ['approve_comments', 'disapprove_comments']
    
    def approve_comments(self, request, queryset):
        queryset.update(active=True)
        self.message_user(request, f'{queryset.count()} comments approved.')
    
    approve_comments.short_description = "Approve selected comments"
    
    def disapprove_comments(self, request, queryset):
        queryset.update(active=False)
        self.message_user(request, f'{queryset.count()} comments disapproved.')
    
    disapprove_comments.short_description = "Disapprove selected comments"
