from django.shortcuts import render, get_object_or_404, redirect
from django.core.paginator import Paginator
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Q, Count
from django.utils import timezone
from .forms import PostForm, CommentForm
from categories.models import Category
from comments.models import Comment
from taggit.models import Tag
from newsletter.models import Subscriber
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from .models import Post, PostLike

@login_required
@require_POST
def like_post(request, post_id):
    """Handle post likes"""
    post = get_object_or_404(Post, id=post_id, status='published')
    
    result = PostLike.toggle_like(post, request.user)
    
    return JsonResponse({
        'success': True,
        'action': result['action'],
        'likes_count': post.likes_count(),
        'dislikes_count': post.dislikes_count(),
        'total_votes': post.total_votes(),
        'net_votes': post.net_votes(),
        'like_percentage': post.like_percentage(),
        'user_vote': result['is_like'],
    })

@login_required
@require_POST
def dislike_post(request, post_id):
    """Handle post dislikes"""
    post = get_object_or_404(Post, id=post_id, status='published')
    
    result = PostLike.toggle_dislike(post, request.user)
    
    return JsonResponse({
        'success': True,
        'action': result['action'],
        'likes_count': post.likes_count(),
        'dislikes_count': post.dislikes_count(),
        'total_votes': post.total_votes(),
        'net_votes': post.net_votes(),
        'like_percentage': post.like_percentage(),
        'user_vote': result['is_like'],
    })

@login_required
def get_post_votes(request, post_id):
    """Get vote counts for a post (AJAX)"""
    post = get_object_or_404(Post, id=post_id)
    
    return JsonResponse({
        'success': True,
        'likes_count': post.likes_count(),
        'dislikes_count': post.dislikes_count(),
        'total_votes': post.total_votes(),
        'net_votes': post.net_votes(),
        'like_percentage': post.like_percentage(),
        'user_vote': post.user_vote(request.user),
    })


@login_required
def manage_posts(request):
    """View for users to manage their posts"""
    # Base queryset - filter by user unless staff
    if request.user.is_staff:
        posts = Post.objects.all()
    else:
        posts = Post.objects.filter(author=request.user)
    
    # Annotate with comment count
    posts = posts.annotate(comments_count=Count('comments'))
    
    # Search filter
    search_query = request.GET.get('search', '')
    if search_query:
        posts = posts.filter(
            Q(title__icontains=search_query) |
            Q(content__icontains=search_query) |
            Q(excerpt__icontains=search_query)
        )
    
    # Category filter
    category_filter = request.GET.get('category', '')
    if category_filter and category_filter.isdigit():
        posts = posts.filter(category_id=category_filter)
    
    # Status filter
    status_filter = request.GET.get('status', '')
    if status_filter in ['published', 'draft']:
        posts = posts.filter(status=status_filter)
    
    # Approved status filter (custom field if you have it)
    approved_filter = request.GET.get('approved', '')
    if approved_filter:
        # Assuming you have an is_approved field
        if approved_filter == 'approved':
            posts = posts.filter(is_approved=True)
        elif approved_filter == 'pending':
            posts = posts.filter(is_approved=None)
        elif approved_filter == 'rejected':
            posts = posts.filter(is_approved=False)
    
    # Sorting
    sort_by = request.GET.get('sort', '-published_date')
    if sort_by in ['published_date', '-published_date', 'title', '-title', 'view_count', '-view_count', 'comments_count', '-comments_count']:
        posts = posts.order_by(sort_by)
    else:
        posts = posts.order_by('-published_date')
    
    # Pagination
    paginator = Paginator(posts, 10)  # 10 posts per page
    page = request.GET.get('page')
    posts_page = paginator.get_page(page)
    
    # Get all categories for filter dropdown
    categories = Category.objects.all()
    
    # Get total count for the badge
    total_posts = posts.count()
    
    context = {
        'posts': posts_page,
        'categories': categories,
        'total_posts': total_posts,
        'search_query': search_query,
        'category_filter': category_filter,
        'status_filter': status_filter,
        'approved_filter': approved_filter,
        'sort_by': sort_by,
    }
    
    return render(request, 'posts/manage_posts.html', context)

def home(request):
    """Home page view with all sections"""
    
    # Hero posts (featured posts)
    hero_posts = Post.objects.filter(
        status='published',
        featured_image__isnull=False
    ).order_by('-published_date')[:5]
    
    # Highlights posts (recent popular posts)
    highlights_posts = Post.objects.filter(
        status='published'
    ).order_by('-view_count', '-published_date')[:8]
    
    # Top highlights (last week's most viewed)
    from django.utils import timezone
    from datetime import timedelta
    
    last_week = timezone.now() - timedelta(days=7)
    top_highlights = Post.objects.filter(
        status='published',
        published_date__gte=last_week
    ).order_by('-view_count')[:5]
    
    # Trending categories
    trending_categories = Category.objects.annotate(
        post_count=Count('posts')
    ).filter(post_count__gt=0).order_by('-post_count')[:8]
    
    # Sports posts
    sports_category = Category.objects.filter(name__icontains='sport').first()
    if sports_category:
        sports_posts = Post.objects.filter(
            category=sports_category,
            status='published'
        ).order_by('-published_date')[:4]
    else:
        sports_posts = Post.objects.filter(
            status='published'
        ).order_by('-published_date')[:4]
    
    # Sponsored posts
    sponsored_posts = Post.objects.filter(
        status='published',
        is_sponsored=True
    ).order_by('-published_date')[:6]
    
    # If not enough sponsored posts, get regular ones
    if sponsored_posts.count() < 6:
        regular_posts = Post.objects.filter(
            status='published',
            is_sponsored=False
        ).order_by('-published_date')[:6 - sponsored_posts.count()]
        sponsored_posts = list(sponsored_posts) + list(regular_posts)
    
    # Popular tags
    popular_tags = Tag.objects.annotate(
        post_count=Count('taggit_taggeditem_items')
    ).order_by('-post_count')[:15]
    
    context = {
        'hero_posts': hero_posts,
        'highlights_posts': highlights_posts,
        'top_highlights': top_highlights,
        'trending_categories': trending_categories,
        'sports_posts': sports_posts,
        'sponsored_posts': sponsored_posts,
        'popular_tags': popular_tags,
    }
    
    return render(request, 'posts/home.html', context)

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
    """Advanced search functionality"""
    query = request.GET.get('q', '')
    category_slug = request.GET.get('category', '')
    tag_slug = request.GET.get('tag', '')
    author = request.GET.get('author', '')
    date_from = request.GET.get('date_from', '')
    date_to = request.GET.get('date_to', '')
    
    # Base queryset
    results = Post.objects.filter(status='published')
    
    # Apply filters
    if query:
        results = results.filter(
            Q(title__icontains=query) |
            Q(content__icontains=query) |
            Q(excerpt__icontains=query) |
            Q(tags__name__icontains=query)
        ).distinct()
    
    if category_slug:
        results = results.filter(category__slug=category_slug)
    
    if tag_slug:
        results = results.filter(tags__slug=tag_slug)
    
    if author:
        results = results.filter(
            Q(author__username__icontains=author) |
            Q(author__first_name__icontains=author) |
            Q(author__last_name__icontains=author)
        )
    
    if date_from:
        results = results.filter(published_date__gte=date_from)
    
    if date_to:
        results = results.filter(published_date__lte=date_to)
    
    # Order by relevance (if query exists) or date
    if query:
        # Simple relevance sorting - posts with title matches first
        results = results.extra(
            select={'relevance': 'CASE WHEN title LIKE %s THEN 2 ELSE 1 END' % f'%{query}%'}
        ).order_by('-relevance', '-published_date')
    else:
        results = results.order_by('-published_date')
    
    # Pagination
    paginator = Paginator(results, 10)  # 10 results per page
    page = request.GET.get('page')
    results_page = paginator.get_page(page)
    
    # Get trending categories
    trending_categories = Category.objects.annotate(
        post_count=Count('posts', filter=Q(posts__status='published'))
    ).filter(post_count__gt=0).order_by('-post_count')[:8]
    
    # Get recent posts
    recent_posts = Post.objects.filter(
        status='published'
    ).order_by('-published_date')[:10]
    
    # Get popular tags
    popular_tags = Tag.objects.annotate(
        post_count=Count('taggit_taggeditem_items')
    ).order_by('-post_count')[:15]
    
    context = {
        'query': query,
        'results': results_page,
        'paginator': paginator,
        'trending_categories': trending_categories,
        'recent_posts': recent_posts,
        'popular_tags': popular_tags,
        'category_slug': category_slug,
        'tag_slug': tag_slug,
        'author': author,
        'date_from': date_from,
        'date_to': date_to,
    }
    
    return render(request, 'search/search_results.html', context)

def advanced_search(request):
    """Advanced search with more filters"""
    return render(request, 'search/advanced_search.html')

def newsletter_subscribe(request):
    """Handle newsletter subscription"""
    if request.method == 'POST':
        email = request.POST.get('email')
        if email:
            subscriber, created = Subscriber.objects.get_or_create(
                email=email,
                defaults={'is_active': True}
            )
            if created:
                messages.success(request, 'Thank you for subscribing!')
            else:
                if not subscriber.is_active:
                    subscriber.is_active = True
                    subscriber.save()
                    messages.success(request, 'Your subscription has been reactivated!')
                else:
                    messages.info(request, 'You are already subscribed!')
        else:
            messages.error(request, 'Please provide a valid email address.')
    
    return redirect('home')