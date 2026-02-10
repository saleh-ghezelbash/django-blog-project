from django.shortcuts import render, get_object_or_404, redirect
from django.core.paginator import Paginator
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Q, Count
from django.utils import timezone
from .models import Post
from .forms import PostForm, CommentForm
from categories.models import Category
from comments.models import Comment
from taggit.models import Tag

def home(request):
    featured_posts = Post.objects.filter(
        status='published', 
        featured_image__isnull=False
    ).order_by('-published_date')[:10]
    
    latest_posts = Post.objects.filter(status='published').order_by('-published_date')[:20]
    
    # If not enough featured posts, use latest posts as fallback
    if not featured_posts.exists():
        featured_posts = latest_posts[:5]
    
    categories = Category.objects.annotate(post_count=Count('posts'))[:8]
    
    # Get popular tags
    from taggit.models import Tag
    popular_tags = Tag.objects.all()[:10]
    
    return render(request, 'posts/home.html', {
        'featured_posts': featured_posts,
        'latest_posts': latest_posts,
        'categories': categories,
        'popular_tags': popular_tags,
    })

def post_list(request):
    posts_list = Post.objects.filter(status='published').order_by('-published_date')
    
    # Filter by category
    category_slug = request.GET.get('category')
    if category_slug:
        category = get_object_or_404(Category, slug=category_slug)
        posts_list = posts_list.filter(category=category)
    
    # Filter by tag
    tag_slug = request.GET.get('tag')
    if tag_slug:
        tag = get_object_or_404(Tag, slug=tag_slug)
        posts_list = posts_list.filter(tags=tag)
    
    # Filter by search
    search_query = request.GET.get('q')
    if search_query:
        posts_list = posts_list.filter(
            Q(title__icontains=search_query) |
            Q(content__icontains=search_query) |
            Q(excerpt__icontains=search_query) |
            Q(tags__name__icontains=search_query)
        ).distinct()
    
    # Pagination
    paginator = Paginator(posts_list, 10)
    page = request.GET.get('page')
    posts = paginator.get_page(page)
    
    categories = Category.objects.annotate(post_count=Count('posts'))
    
    return render(request, 'posts/post_list.html', {
        'posts': posts,
        'categories': categories,
    })


def post_detail(request, year, month, day, slug):
    post = get_object_or_404(
        Post,
        published_date__year=year,
        published_date__month=month,
        published_date__day=day,
        slug=slug,
        status='published'
    )
    
    # Increment view count
    post.increment_view_count()
    
    # Get related posts
    related_posts = Post.objects.filter(
        tags__in=post.tags.all(),
        status='published'
    ).exclude(id=post.id).distinct()[:3]
    
    # Get author's published posts (excluding current post)
    author_posts = Post.objects.filter(
        author=post.author,
        status='published'
    ).exclude(id=post.id).order_by('-published_date')[:3]
    
    # Get comments
    comments = post.comments.filter(active=True).order_by('-created_at')
    
    # Comment form
    if request.method == 'POST':
        comment_form = CommentForm(data=request.POST)
        if comment_form.is_valid():
            new_comment = comment_form.save(commit=False)
            new_comment.post = post
            new_comment.author = request.user if request.user.is_authenticated else None
            new_comment.save()
            messages.success(request, 'Your comment has been added!')
            return redirect(post.get_absolute_url())
    else:
        comment_form = CommentForm()
    
    return render(request, 'posts/post_detail.html', {
        'post': post,
        'related_posts': related_posts,
        'author_posts': author_posts,  # Add this
        'comments': comments,
        'comment_form': comment_form,
    })

@login_required
def post_create(request):
    if request.method == 'POST':
        form = PostForm(request.POST, request.FILES, user=request.user)
        if form.is_valid():
            post = form.save()
            messages.success(request, 'Post created successfully!')
            return redirect(post.get_absolute_url())
    else:
        form = PostForm(user=request.user)
    
    return render(request, 'posts/post_form.html', {'form': form, 'title': 'Create New Post'})

@login_required
def post_update(request, pk):
    post = get_object_or_404(Post, pk=pk, author=request.user)
    
    if request.method == 'POST':
        form = PostForm(request.POST, request.FILES, instance=post, user=request.user)
        if form.is_valid():
            post = form.save()
            messages.success(request, 'Post updated successfully!')
            return redirect(post.get_absolute_url())
    else:
        form = PostForm(instance=post, user=request.user)
    
    return render(request, 'posts/post_form.html', {'form': form, 'title': 'Update Post'})

@login_required
def post_delete(request, pk):
    post = get_object_or_404(Post, pk=pk, author=request.user)
    
    if request.method == 'POST':
        post.delete()
        messages.success(request, 'Post deleted successfully!')
        return redirect('post_list')
    
    return render(request, 'posts/post_confirm_delete.html', {'post': post})

def search(request):
    query = request.GET.get('q')
    results = []
    
    if query:
        results = Post.objects.filter(
            Q(title__icontains=query) |
            Q(content__icontains=query) |
            Q(excerpt__icontains=query) |
            Q(tags__name__icontains=query),
            status='published'
        ).distinct().order_by('-published_date')
    
    return render(request, 'posts/search_results.html', {
        'query': query,
        'results': results
    })