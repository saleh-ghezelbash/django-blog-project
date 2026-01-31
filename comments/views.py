from django.shortcuts import get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from .models import Comment
from posts.models import Post

@login_required
def comment_delete(request, pk):
    comment = get_object_or_404(Comment, pk=pk)
    
    # Check if user owns the comment or is staff
    if request.user == comment.author or request.user.is_staff:
        post_url = comment.post.get_absolute_url()
        comment.delete()
        messages.success(request, 'Comment deleted successfully!')
        return redirect(post_url)
    
    messages.error(request, 'You are not authorized to delete this comment.')
    return redirect(comment.post.get_absolute_url())

@login_required
def comment_toggle(request, pk):
    comment = get_object_or_404(Comment, pk=pk)
    
    if request.user.is_staff:  # Only staff can toggle comment status
        comment.active = not comment.active
        comment.save()
        
        if request.is_ajax():
            return JsonResponse({'active': comment.active})
        
        messages.success(request, f'Comment {"activated" if comment.active else "deactivated"}!')
    
    return redirect(comment.post.get_absolute_url())