from django.core.paginator import Paginator
from django.shortcuts import render
from .models import Category
from posts.models import Post
from taggit.models import Tag
from django.db.models import Count
from django.shortcuts import render, get_object_or_404

def category_list(request):
    # Get all categories
    categories_list = Category.objects.annotate(post_count=Count('posts')).order_by('name')
    
    # Pagination for categories
    paginator = Paginator(categories_list, 12)  # 12 categories per page
    page = request.GET.get('page')
    categories = paginator.get_page(page)
    
    # Get recent posts for sidebar
    recent_posts = Post.objects.filter(status='published').order_by('-published_date')[:10]
    
    # Get popular tags
    popular_tags = Tag.objects.all()[:15]
    
    # Default tags if no tags exist
    default_tags = ['Technology', 'Lifestyle', 'Travel', 'Food', 'Health', 'Education']
    
    return render(request, 'categories/category_list.html', {
        'categories': categories,
        'recent_posts': recent_posts,
        'popular_tags': popular_tags,
        'default_tags': default_tags,
    })


from django.shortcuts import render, get_object_or_404
from django.core.paginator import Paginator
from django.db.models import Count, Q
from .models import Category
from posts.models import Post

def category_posts(request, slug):
    """Display posts in a specific category"""
    category = get_object_or_404(Category, slug=slug)
    
    # Get published posts in this category
    posts_list = Post.objects.filter(
        category=category, 
        status='published'
    ).select_related('author', 'category').prefetch_related('tags', 'comments').order_by('-published_date')
    
    # Pagination
    paginator = Paginator(posts_list, 6)  # 6 posts per page (2 columns of 3 rows)
    page = request.GET.get('page')
    posts = paginator.get_page(page)
    
    # Get author count for this category
    author_count = Post.objects.filter(
        category=category,
        status='published'
    ).values('author').distinct().count()
    
    # Add author_count to category object
    category.author_count = author_count
    
    context = {
        'category': category,
        'posts': posts,
        'page_title': f'{category.name} - Category',
        'meta_description': category.description or f'Explore all posts in the {category.name} category.',
    }
    
    return render(request, 'categories/category_posts.html', context)    