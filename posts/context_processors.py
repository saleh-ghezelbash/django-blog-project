from categories.models import Category
from taggit.models import Tag
from django.db.models import Count, Q
from posts.models import Post

def category_context(request):
    """Add categories to all templates"""
    categories = Category.objects.annotate(
        post_count=Count('posts', filter=Q(posts__status='published'))
    ).filter(post_count__gt=0)[:10]
    
    popular_tags = Tag.objects.annotate(
        post_count=Count('taggit_taggeditem_items')
    ).order_by('-post_count')[:15]
    
    return {
        'categories': categories,
        'popular_tags': popular_tags,
    }    


def common_data(request):
    """Common data for all templates"""
    
    # Categories with post counts
    categories = Category.objects.annotate(
        post_count=Count('posts', filter=Q(posts__status='published'))
    ).filter(post_count__gt=0).order_by('-post_count')[:10]
    
    # Popular tags
    popular_tags = Tag.objects.annotate(
        post_count=Count('taggit_taggeditem_items')
    ).order_by('-post_count')[:15]
    
    # Recent posts
    recent_posts = Post.objects.filter(
        status='published'
    ).order_by('-published_date')[:5]
    
    # Trending categories (with images)
    trending_categories = Category.objects.annotate(
        post_count=Count('posts', filter=Q(posts__status='published'))
    ).filter(post_count__gt=0).order_by('-post_count')[:8]
    
    return {
        'categories': categories,
        'popular_tags': popular_tags,
        'recent_posts': recent_posts,
        'trending_categories': trending_categories,
    }