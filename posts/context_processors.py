from categories.models import Category
from taggit.models import Tag
from django.db.models import Count, Q

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