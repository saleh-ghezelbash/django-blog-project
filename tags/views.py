from django.shortcuts import render, get_object_or_404
from django.core.paginator import Paginator
from taggit.models import Tag
from posts.models import Post

def tag_list(request):
    tags = Tag.objects.all()
    return render(request, 'tags/tag_list.html', {'tags': tags})

def tag_posts(request, slug):
    tag = get_object_or_404(Tag, slug=slug)
    posts_list = Post.objects.filter(tags=tag, status='published').order_by('-published_date')
    
    # Pagination
    paginator = Paginator(posts_list, 10)
    page = request.GET.get('page')
    posts = paginator.get_page(page)
    
    return render(request, 'tags/tag_posts.html', {
        'tag': tag,
        'posts': posts
    })
