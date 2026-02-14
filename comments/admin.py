from django.contrib import admin
from django.utils.html import format_html
from .models import Comment, CommentVote, CommentReport

class CommentVoteInline(admin.TabularInline):
    model = CommentVote
    extra = 0
    readonly_fields = ['user', 'vote', 'created_at']

class CommentReportInline(admin.TabularInline):
    model = CommentReport
    extra = 0
    readonly_fields = ['reporter', 'reason', 'details', 'created_at']

@admin.register(Comment)
class CommentAdmin(admin.ModelAdmin):
    list_display = ['id', 'post', 'author_name', 'content_short', 'created_at', 'is_approved', 'active', 'reply_count']
    list_filter = ['is_approved', 'active', 'created_at', 'post']
    search_fields = ['content', 'name', 'email', 'author__username']
    readonly_fields = ['ip_address', 'user_agent', 'created_at', 'updated_at']
    inlines = [CommentVoteInline, CommentReportInline]
    actions = ['approve_comments', 'disapprove_comments', 'delete_selected']
    
    fieldsets = (
        ('Comment', {
            'fields': ('post', 'parent', 'content')
        }),
        ('Author Information', {
            'fields': ('author', 'name', 'email', 'website')
        }),
        ('Status', {
            'fields': ('active', 'is_approved', 'moderated_by', 'moderated_at')
        }),
        ('Technical', {
            'fields': ('ip_address', 'user_agent', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def author_name(self, obj):
        if obj.author:
            return format_html('<a href="{}">{}</a>', 
                             reverse('admin:auth_user_change', args=[obj.author.id]),
                             obj.author.username)
        return obj.name or 'Anonymous'
    author_name.short_description = 'Author'
    
    def content_short(self, obj):
        return obj.content[:50] + '...' if len(obj.content) > 50 else obj.content
    content_short.short_description = 'Content'
    
    def reply_count(self, obj):
        return obj.replies.count()
    reply_count.short_description = 'Replies'
    
    def approve_comments(self, request, queryset):
        for comment in queryset:
            comment.approve(moderator=request.user)
        self.message_user(request, f'{queryset.count()} comments approved.')
    approve_comments.short_description = "Approve selected comments"
    
    def disapprove_comments(self, request, queryset):
        for comment in queryset:
            comment.disapprove(moderator=request.user)
        self.message_user(request, f'{queryset.count()} comments disapproved.')
    disapprove_comments.short_description = "Disapprove selected comments"

@admin.register(CommentVote)
class CommentVoteAdmin(admin.ModelAdmin):
    list_display = ['comment', 'user', 'vote', 'created_at']
    list_filter = ['vote', 'created_at']
    search_fields = ['comment__content', 'user__username']

@admin.register(CommentReport)
class CommentReportAdmin(admin.ModelAdmin):
    list_display = ['comment', 'reporter', 'reason', 'created_at', 'resolved']
    list_filter = ['reason', 'resolved', 'created_at']
    search_fields = ['comment__content', 'reporter__username', 'details']
    readonly_fields = ['comment', 'reporter', 'reason', 'details', 'created_at']
    actions = ['mark_resolved']
    
    def mark_resolved(self, request, queryset):
        queryset.update(resolved=True, resolved_by=request.user, resolved_at=timezone.now())
        self.message_user(request, f'{queryset.count()} reports marked as resolved.')
    mark_resolved.short_description = "Mark selected reports as resolved"