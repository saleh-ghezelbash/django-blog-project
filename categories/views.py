from django.core.paginator import Paginator
from django.shortcuts import render
from .models import Category
from posts.models import Post
from taggit.models import Tag

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

def category_posts(request, slug):
    category = get_object_or_404(Category, slug=slug)
    posts_list = Post.objects.filter(category=category, status='published').order_by('-published_date')
    
    # Pagination
    paginator = Paginator(posts_list, 10)  # 10 posts per page
    page = request.GET.get('page')
    posts = paginator.get_page(page)
    
    return render(request, 'categories/category_posts.html', {
        'category': category,
        'posts': posts
    })