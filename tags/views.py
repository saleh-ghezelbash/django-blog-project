from django.shortcuts import render, get_object_or_404
from django.core.paginator import Paginator
from django.db.models import Count, Q
from taggit.models import Tag
from posts.models import Post
from django.contrib.auth import get_user_model

User = get_user_model()

def tag_list(request):
    """Display all tags with their post counts and related info"""
    # Get all tags
    tags_list = Tag.objects.all().order_by('name')
    
    # Manually calculate post count for each tag
    enhanced_tags = []
    for tag in tags_list:
        # Count published posts for this tag
        post_count = Post.objects.filter(
            tags=tag,
            status='published'
        ).count()
        
        if post_count > 0:  # Only include tags with posts
            # Add calculated fields to tag
            tag.post_count = post_count
            
            # Get recent posts for this tag
            tag.recent_posts = Post.objects.filter(
                tags=tag,
                status='published'
            ).order_by('-published_date')[:5]
            
            # Get top authors for this tag
            author_ids = Post.objects.filter(
                tags=tag,
                status='published'
            ).values('author').annotate(
                author_count=Count('id')
            ).order_by('-author_count')[:5].values_list('author', flat=True)
            
            tag.top_authors = User.objects.filter(id__in=author_ids)
            tag.author_count = len(author_ids)
            
            # Calculate weight for tag cloud (based on post count)
            tag.weight = 1.0  # Default weight
            
            # Assign color based on tag name hash
            colors = ['primary', 'success', 'danger', 'warning', 'info', 'dark']
            tag.color = colors[hash(tag.name) % len(colors)]
            
            # Assign icon based on tag name
            icon_map = {
                'travel': 'fas fa-plane',
                'business': 'fas fa-briefcase',
                'tech': 'fas fa-microchip',
                'technology': 'fas fa-laptop',
                'gadgets': 'fas fa-mobile-alt',
                'lifestyle': 'fas fa-heart',
                'marketing': 'fas fa-chart-line',
                'sports': 'fas fa-futbol',
                'politics': 'fas fa-gavel',
                'food': 'fas fa-utensils',
                'photography': 'fas fa-camera',
                'design': 'fas fa-paint-brush',
                'music': 'fas fa-music',
                'movie': 'fas fa-film',
                'covid': 'fas fa-virus',
                'vaccine': 'fas fa-syringe',
                'health': 'fas fa-heartbeat',
                'fitness': 'fas fa-dumbbell',
                'education': 'fas fa-graduation-cap',
                'science': 'fas fa-flask',
            }
            
            found = False
            for key, icon in icon_map.items():
                if key in tag.name.lower():
                    tag.icon = icon
                    found = True
                    break
            if not found:
                tag.icon = 'fas fa-tag'
            
            enhanced_tags.append(tag)
    
    # Sort by post count (most popular first)
    enhanced_tags.sort(key=lambda x: x.post_count, reverse=True)
    
    # Calculate weights based on max count
    if enhanced_tags:
        max_count = enhanced_tags[0].post_count
        for tag in enhanced_tags:
            tag.weight = 1.0 + (tag.post_count / max_count)  # Range: 1.0 to 2.0
            tag.opacity = 0.5 + (tag.post_count / max_count)  # Range: 0.5 to 1.5
    
    # Pagination
    paginator = Paginator(enhanced_tags, 12)  # 12 tags per page
    page = request.GET.get('page')
    tags = paginator.get_page(page)
    
    # Get popular tags (top 20 by post count)
    popular_tags = enhanced_tags[:20]
    
    context = {
        'tags': tags,
        'popular_tags': popular_tags,
        'total_tags': len(enhanced_tags),
        'page_title': 'Tags',
        'meta_description': 'Browse all tags on our blog. Find posts about Technology, Travel, Lifestyle, Business, and more.',
    }
    
    return render(request, 'tags/tag_list.html', context)


def tag_posts(request, slug):
    """Display posts with a specific tag"""
    tag = get_object_or_404(Tag, slug=slug)
    
    # Get published posts with this tag
    posts_list = Post.objects.filter(
        tags=tag,
        status='published'
    ).select_related('author', 'category').prefetch_related('tags').order_by('-published_date')
    
    # Check if it's an AJAX request for load more
    page = request.GET.get('page', 1)
    
    # Pagination
    paginator = Paginator(posts_list, 6)  # 6 posts per page (2 columns of 3 rows)
    posts = paginator.get_page(page)
    
    # Get related tags (other tags used in these posts)
    related_tag_ids = set()
    for post in posts_list[:30]:  # Limit to recent posts for performance
        for post_tag in post.tags.all():
            if post_tag.id != tag.id:
                related_tag_ids.add(post_tag.id)
    
    related_tags = Tag.objects.filter(id__in=related_tag_ids)[:10]
    
    # Add count to each related tag
    for related_tag in related_tags:
        related_tag.count = Post.objects.filter(
            tags=related_tag,
            status='published'
        ).count()
    
    # Get top authors for this tag
    author_stats = []
    for post in posts_list:
        if post.author and post.author not in [a['author'] for a in author_stats]:
            author_count = posts_list.filter(author=post.author).count()
            author_stats.append({
                'author': post.author,
                'count': author_count
            })
    
    # Sort by count and get top 5
    author_stats.sort(key=lambda x: x['count'], reverse=True)
    top_authors = [item['author'] for item in author_stats[:5]]
    
    # Add post count to each author
    for author in top_authors:
        author.post_count = posts_list.filter(author=author).count()
    
    # Get popular tags for sidebar
    popular_tags = Tag.objects.all()[:15]
    
    context = {
        'tag': tag,
        'posts': posts,
        'related_tags': related_tags,
        'top_authors': top_authors,
        'popular_tags': popular_tags,
        'total_posts': posts_list.count(),
        'page_title': f'#{tag.name} - Tag',
        'meta_description': f'Explore all posts tagged with #{tag.name}.',
    }
    
    # Check if AJAX request
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return render(request, 'tags/tag_posts_partial.html', context)
    
    return render(request, 'tags/tag_posts.html', context)