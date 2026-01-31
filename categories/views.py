from django.shortcuts import render, get_object_or_404
from django.core.paginator import Paginator
from .models import Category
from posts.models import Post

def category_list(request):
    categories = Category.objects.all()
    return render(request, 'categories/category_list.html', {'categories': categories})

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