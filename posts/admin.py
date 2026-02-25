from django.contrib import admin
from django.utils.html import format_html
from .models import Post, PostImage, PostLike

class PostImageInline(admin.TabularInline):
    model = PostImage
    extra = 1


class PostLikeInline(admin.TabularInline):
    model = PostLike
    extra = 0
    readonly_fields = ['user', 'is_like', 'created_at']
    can_delete = False
    
    def has_add_permission(self, request, obj=None):
        return False

@admin.register(Post)
class PostAdmin(admin.ModelAdmin):
    list_display = ['title', 'author', 'category', 'status', 'published_date', 
                    'view_count', 'likes_count', 'dislikes_count', 'net_votes_display']
    list_filter = ['status', 'category', 'published_date', 'author', 'is_sponsored']
    search_fields = ['title', 'content', 'excerpt']
    prepopulated_fields = {'slug': ('title',)}
    date_hierarchy = 'published_date'
    ordering = ['-published_date']
    inlines = [PostImageInline, PostLikeInline]
    
    fieldsets = (
        (None, {
            'fields': ('title', 'slug', 'author', 'category', 'tags')
        }),
        ('Content', {
            'fields': ('content', 'excerpt', 'featured_image')
        }),
        ('Publishing', {
            'fields': ('status', 'published_date', 'is_sponsored')
        }),
        ('Statistics', {
            'fields': ('view_count', 'rating')
        }),
    )
    
    def likes_count(self, obj):
        return obj.likes_count()
    likes_count.short_description = 'Likes'
    
    def dislikes_count(self, obj):
        return obj.dislikes_count()
    dislikes_count.short_description = 'Dislikes'
    
    def net_votes_display(self, obj):
        net = obj.net_votes()
        if net > 0:
            return format_html('<span style="color: green;">+{}</span>', net)
        elif net < 0:
            return format_html('<span style="color: red;">{}</span>', net)
        else:
            return format_html('<span style="color: gray;">0</span>', net)
    net_votes_display.short_description = 'Net Votes'

@admin.register(PostLike)
class PostLikeAdmin(admin.ModelAdmin):
    list_display = ['post', 'user', 'is_like', 'created_at']
    list_filter = ['is_like', 'created_at']
    search_fields = ['post__title', 'user__username']
    readonly_fields = ['created_at', 'updated_at']
    
    def has_add_permission(self, request):
        return False

@admin.register(PostImage)
class PostImageAdmin(admin.ModelAdmin):
    list_display = ['post', 'image_preview', 'caption', 'uploaded_at']
    list_filter = ['uploaded_at']
    
    def image_preview(self, obj):
        if obj.image:
            return format_html('<img src="{}" style="width: 50px; height: 50px; object-fit: cover;" />', obj.image.url)
        return "No Image"
    image_preview.short_description = 'Preview'