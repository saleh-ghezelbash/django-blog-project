from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse, HttpResponseForbidden
from django.views.decorators.http import require_POST
from django.views.decorators.csrf import csrf_exempt
from django.db.models import Count, Q
from django.utils import timezone
import json

from .models import Comment, CommentVote, CommentReport
from .forms import CommentForm, CommentReplyForm
from posts.models import Post

def get_client_ip(request):
    """Get client IP address"""
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip

@require_POST
def add_comment(request, post_id):
    """Add a new comment to a post"""
    post = get_object_or_404(Post, id=post_id, status='published')
    
    form = CommentForm(request.POST, user=request.user)
    
    if form.is_valid():
        comment = form.save(commit=False)
        comment.post = post
        comment.ip_address = get_client_ip(request)
        comment.user_agent = request.META.get('HTTP_USER_AGENT', '')[:500]
        
        # Set author if authenticated
        if request.user.is_authenticated:
            comment.author = request.user
        
        # Auto-approve for trusted users
        if request.user.is_authenticated and request.user.is_staff:
            comment.is_approved = True
        
        comment.save()
        
        # Send notification emails
        send_comment_notifications(comment)
        
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            # Return JSON for AJAX requests
            return JsonResponse({
                'success': True,
                'comment': {
                    'id': comment.id,
                    'content': comment.content,
                    'author': comment.author.username if comment.author else comment.name,
                    'created_at': comment.created_at.strftime('%B %d, %Y at %I:%M %p'),
                    'avatar': comment.author.profile_picture.url if comment.author and comment.author.profile_picture else None,
                    'is_approved': comment.is_approved,
                }
            })
        else:
            messages.success(request, 'Your comment has been posted! It will appear after moderation.')
            return redirect(comment.post.get_absolute_url() + '#comments')
    else:
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({
                'success': False,
                'errors': form.errors
            }, status=400)
        else:
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, f"{field}: {error}")
            return redirect(post.get_absolute_url() + '#comment-form')

@require_POST
def reply_comment(request, comment_id):
    """Reply to a comment"""
    parent_comment = get_object_or_404(Comment, id=comment_id, active=True)
    post = parent_comment.post
    
    form = CommentReplyForm(request.POST)
    
    if form.is_valid():
        reply = form.save(commit=False)
        reply.post = post
        reply.parent = parent_comment
        reply.ip_address = get_client_ip(request)
        reply.user_agent = request.META.get('HTTP_USER_AGENT', '')[:500]
        
        if request.user.is_authenticated:
            reply.author = request.user
        else:
            # For anonymous replies, use the parent comment's name as default
            reply.name = request.POST.get('name', 'Anonymous')
            reply.email = request.POST.get('email', '')
        
        reply.save()
        
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({
                'success': True,
                'reply': {
                    'id': reply.id,
                    'content': reply.content,
                    'author': reply.author.username if reply.author else reply.name,
                    'created_at': reply.created_at.strftime('%B %d, %Y at %I:%M %p'),
                    'parent_id': parent_comment.id,
                }
            })
        else:
            messages.success(request, 'Your reply has been posted!')
            return redirect(post.get_absolute_url() + f'#comment-{parent_comment.id}')
    else:
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({
                'success': False,
                'errors': form.errors
            }, status=400)
        else:
            messages.error(request, 'Error posting reply. Please try again.')
            return redirect(post.get_absolute_url())

@login_required
@require_POST
def vote_comment(request, comment_id):
    """Vote (like/dislike) on a comment"""
    comment = get_object_or_404(Comment, id=comment_id, active=True)
    vote_type = int(request.POST.get('vote', 1))  # 1 for upvote, -1 for downvote
    
    try:
        vote, created = CommentVote.objects.get_or_create(
            comment=comment,
            user=request.user,
            defaults={'vote': vote_type}
        )
        
        if not created:
            # Update existing vote
            if vote.vote == vote_type:
                # Remove vote if same
                vote.delete()
                vote_type = 0
            else:
                # Change vote
                vote.vote = vote_type
                vote.save()
        
        # Get updated vote counts
        upvotes = comment.votes.filter(vote=1).count()
        downvotes = comment.votes.filter(vote=-1).count()
        
        return JsonResponse({
            'success': True,
            'upvotes': upvotes,
            'downvotes': downvotes,
            'user_vote': vote_type if 'vote' in locals() else 0,
            'score': upvotes - downvotes,
        })
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=400)

@login_required
@require_POST
def delete_comment(request, comment_id):
    """Delete a comment (author or staff only)"""
    comment = get_object_or_404(Comment, id=comment_id)
    
    # Check permissions
    if not (request.user == comment.author or request.user.is_staff):
        return HttpResponseForbidden("You don't have permission to delete this comment.")
    
    post_url = comment.post.get_absolute_url()
    comment.delete()
    
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return JsonResponse({'success': True})
    else:
        messages.success(request, 'Comment deleted successfully!')
        return redirect(post_url + '#comments')

@login_required
@require_POST
def report_comment(request, comment_id):
    """Report an inappropriate comment"""
    comment = get_object_or_404(Comment, id=comment_id, active=True)
    
    reason = request.POST.get('reason', 'other')
    details = request.POST.get('details', '')
    
    # Check if already reported
    existing_report = CommentReport.objects.filter(
        comment=comment,
        reporter=request.user
    ).first()
    
    if existing_report:
        return JsonResponse({
            'success': False,
            'error': 'You have already reported this comment.'
        }, status=400)
    
    report = CommentReport.objects.create(
        comment=comment,
        reporter=request.user,
        reason=reason,
        details=details
    )
    
    # Notify admins (implement email notification here)
    
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return JsonResponse({
            'success': True,
            'message': 'Thank you for reporting this comment. Our moderators will review it.'
        })
    else:
        messages.success(request, 'Comment reported successfully.')
        return redirect(comment.post.get_absolute_url() + '#comments')

@login_required
def moderate_comment(request, comment_id):
    """Moderate a comment (staff only)"""
    if not request.user.is_staff:
        return HttpResponseForbidden("You don't have permission to moderate comments.")
    
    comment = get_object_or_404(Comment, id=comment_id)
    action = request.POST.get('action')
    
    if action == 'approve':
        comment.approve(moderator=request.user)
        messages.success(request, 'Comment approved.')
    elif action == 'disapprove':
        comment.disapprove(moderator=request.user)
        messages.success(request, 'Comment disapproved.')
    elif action == 'delete':
        post_url = comment.post.get_absolute_url()
        comment.delete()
        messages.success(request, 'Comment deleted.')
        return redirect(post_url + '#comments')
    
    return redirect(comment.post.get_absolute_url() + '#comments')

def get_comment_thread(request, comment_id):
    """Get a comment thread with all replies (AJAX)"""
    comment = get_object_or_404(Comment, id=comment_id, active=True)
    
    def serialize_comment(c):
        return {
            'id': c.id,
            'content': c.content,
            'author': c.author.username if c.author else c.name,
            'created_at': c.created_at.strftime('%B %d, %Y at %I:%M %p'),
            'avatar': c.author.profile_picture.url if c.author and c.author.profile_picture else None,
            'upvotes': c.votes.filter(vote=1).count(),
            'downvotes': c.votes.filter(vote=-1).count(),
            'replies': [serialize_comment(reply) for reply in c.get_replies()],
            'can_delete': request.user == c.author or request.user.is_staff,
        }
    
    data = serialize_comment(comment)
    
    return JsonResponse(data)

def send_comment_notifications(comment):
    """Send email notifications for new comments"""
    try:
        from django.core.mail import send_mail
        from django.conf import settings
        from django.template.loader import render_to_string
        
        # Notify post author
        if comment.author != comment.post.author:
            subject = f"New comment on your post: {comment.post.title}"
            context = {
                'comment': comment,
                'post': comment.post,
                'site_url': settings.SITE_URL,
            }
            message = render_to_string('emails/new_comment_notification.txt', context)
            html_message = render_to_string('emails/new_comment_notification.html', context)
            
            send_mail(
                subject=subject,
                message=message,
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[comment.post.author.email],
                html_message=html_message,
                fail_silently=True,
            )
        
        # Notify parent comment author for replies
        if comment.parent and comment.author != comment.parent.author:
            if comment.parent.author:
                subject = f"New reply to your comment on: {comment.post.title}"
                context = {
                    'comment': comment,
                    'parent': comment.parent,
                    'post': comment.post,
                    'site_url': settings.SITE_URL,
                }
                message = render_to_string('emails/new_reply_notification.txt', context)
                html_message = render_to_string('emails/new_reply_notification.html', context)
                
                send_mail(
                    subject=subject,
                    message=message,
                    from_email=settings.DEFAULT_FROM_EMAIL,
                    recipient_list=[comment.parent.author.email],
                    html_message=html_message,
                    fail_silently=True,
                )
        
        # Notify admins for moderation
        if settings.NOTIFY_ADMIN_ON_COMMENT:
            subject = f"New comment requires moderation on: {comment.post.title}"
            context = {
                'comment': comment,
                'post': comment.post,
                'site_url': settings.SITE_URL,
            }
            message = render_to_string('emails/comment_moderation_notification.txt', context)
            html_message = render_to_string('emails/comment_moderation_notification.html', context)
            
            send_mail(
                subject=subject,
                message=message,
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[settings.ADMIN_EMAIL],
                html_message=html_message,
                fail_silently=True,
            )
    except Exception as e:
        print(f"Error sending comment notification: {e}")