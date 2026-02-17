from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.contrib.auth import update_session_auth_hash
from django.contrib.auth.forms import PasswordChangeForm
from .forms import ProfileUpdateForm
from .models import CustomUser
from django.contrib.auth import get_user_model
from posts.models import Post
from django.core.paginator import Paginator
from django.db.models import Count, Sum, Q
from django.views.decorators.http import require_POST
from comments.models import Comment  # Add this import

User = get_user_model()

@login_required
def profile(request):
    if request.method == 'POST':
        form = ProfileUpdateForm(request.POST, request.FILES, instance=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, 'Your profile has been updated!')
            return redirect('profile')
    else:
        form = ProfileUpdateForm(instance=request.user)
    
    return render(request, 'users/profile.html', {'form': form})

@login_required
def change_password(request):
    if request.method == 'POST':
        form = PasswordChangeForm(request.user, request.POST)
        if form.is_valid():
            user = form.save()
            update_session_auth_hash(request, user)
            messages.success(request, 'Your password was successfully updated!')
            return redirect('profile')
        else:
            messages.error(request, 'Please correct the error below.')
    else:
        form = PasswordChangeForm(request.user)
    return render(request, 'users/change_password.html', {'form': form})


def register(request):
    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(request, 'Registration successful!')
            return redirect('home')
    else:
        form = CustomUserCreationForm()
    return render(request, 'registration/register.html', {'form': form})



def author_profile(request, username):
    """Display author profile with their posts"""
    author = get_object_or_404(CustomUser, username=username)
    
    # Get filter parameters
    sort = request.GET.get('sort', 'newest')
    
    # Base queryset for author's published posts
    posts = Post.objects.filter(
        author=author,
        status='published'
    ).select_related('category').prefetch_related('tags')
    
    # Apply sorting
    if sort == 'newest':
        posts = posts.order_by('-published_date')
    elif sort == 'oldest':
        posts = posts.order_by('published_date')
    elif sort == 'popular':
        posts = posts.order_by('-views_count', '-published_date')
    elif sort == 'commented':
        posts = posts.annotate(
            comment_count=Count('comments', distinct=True)
        ).order_by('-comment_count', '-published_date')
    
    # Calculate author stats
    total_posts = posts.count()
    total_views = posts.aggregate(Sum('views_count'))['views_count__sum'] or 0
    
    # Calculate total comments for author's posts
    total_comments = Comment.objects.filter(
        post__in=posts,
        active=True,
        is_approved=True
    ).count()
    
    # Get popular posts for sidebar
    popular_posts = posts.order_by('-views_count')[:3]
    
    # Get category distribution
    category_dist = posts.values('category__name').annotate(
        count=Count('id')
    ).order_by('-count')[:5]
    
    # Pagination
    paginator = Paginator(posts, 9)  # 9 posts per page
    page = request.GET.get('page')
    posts_page = paginator.get_page(page)
    
    # Check if current user follows this author
    is_following = False
    if request.user.is_authenticated and request.user != author:
        if hasattr(author, 'followers'):
            is_following = author.followers.filter(id=request.user.id).exists()
    
    # Get follower count
    follower_count = author.followers.count() if hasattr(author, 'followers') else 0
    
    # Fix: Use Python's or operator instead of Django's default filter
    author_display_name = author.get_full_name() or author.username
    
    context = {
        'author': author,
        'posts': posts_page,
        'popular_posts': popular_posts,
        'total_posts': total_posts,
        'total_views': total_views,
        'total_comments': total_comments,
        'follower_count': follower_count,
        'category_dist': category_dist,
        'sort': sort,
        'is_following': is_following,
        'author_display_name': author_display_name,  # Add this
        'page_title': f"{author_display_name} - Author Profile",
        'meta_description': author.bio[:160] if author.bio else f"Read articles by {author.username}",
    }
    
    # Check if AJAX request for load more
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return render(request, 'users/author_posts_partial.html', context)
    
    return render(request, 'users/author_profile.html', context)

@login_required
@require_POST
def follow_author(request, author_id):
    """Follow/unfollow an author"""
    author = get_object_or_404(CustomUser, id=author_id)
    
    if request.user == author:
        return JsonResponse({
            'success': False,
            'error': 'You cannot follow yourself'
        }, status=400)
    
    # Check if followers relationship exists
    if not hasattr(author, 'followers'):
        return JsonResponse({
            'success': False,
            'error': 'Follow feature not available'
        }, status=400)
    
    if author.followers.filter(id=request.user.id).exists():
        # Unfollow
        author.followers.remove(request.user)
        following = False
        message = f'You have unfollowed {author.username}'
    else:
        # Follow
        author.followers.add(request.user)
        following = True
        message = f'You are now following {author.username}'
    
    return JsonResponse({
        'success': True,
        'following': following,
        'follower_count': author.followers.count(),
        'message': message
    })

def author_list(request):
    """List all authors with their stats"""
    authors = CustomUser.objects.annotate(
        post_count=Count('blog_posts', filter=Q(blog_posts__status='published')),
        total_views=Sum('blog_posts__views_count')
    ).filter(post_count__gt=0).order_by('-post_count')
    
    # Add comment count separately (more efficient than annotating)
    authors_with_comments = []
    for author in authors:
        author_posts = Post.objects.filter(author=author, status='published')
        author.total_comments = Comment.objects.filter(
            post__in=author_posts,
            active=True,
            is_approved=True
        ).count()
        authors_with_comments.append(author)
    
    # Filter by search
    search_query = request.GET.get('q', '')
    if search_query:
        authors = authors.filter(
            Q(username__icontains=search_query) |
            Q(first_name__icontains=search_query) |
            Q(last_name__icontains=search_query) |
            Q(bio__icontains=search_query)
        )
    
    # Pagination
    paginator = Paginator(authors, 12)
    page = request.GET.get('page')
    authors_page = paginator.get_page(page)
    
    # Add comment counts to paginated authors
    for author in authors_page:
        author_posts = Post.objects.filter(author=author, status='published')
        author.total_comments = Comment.objects.filter(
            post__in=author_posts,
            active=True,
            is_approved=True
        ).count()
    
    context = {
        'authors': authors_page,
        'search_query': search_query,
        'total_authors': authors.count(),
    }
    
    return render(request, 'users/author_list.html', context)