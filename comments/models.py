from django.db import models
from django.urls import reverse
from django.utils import timezone
from django.contrib.auth import get_user_model
from posts.models import Post

User = get_user_model()

class Comment(models.Model):
    post = models.ForeignKey(Post, on_delete=models.CASCADE, related_name='comments')
    parent = models.ForeignKey('self', on_delete=models.CASCADE, null=True, blank=True, related_name='replies')
    author = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='comments')
    name = models.CharField(max_length=100, blank=True)  # For non-authenticated users
    email = models.EmailField(blank=True)  # For non-authenticated users
    website = models.URLField(blank=True, null=True)  # Optional website field
    content = models.TextField()
    
    # Comment metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    active = models.BooleanField(default=True)
    
    # IP tracking for spam prevention
    ip_address = models.GenericIPAddressField(blank=True, null=True)
    user_agent = models.TextField(blank=True, null=True)
    
    # Moderation
    is_approved = models.BooleanField(default=False)
    moderated_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='moderated_comments')
    moderated_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['created_at']),
            models.Index(fields=['post', 'active']),
            models.Index(fields=['parent']),
        ]
    
    def __str__(self):
        author_name = self.author.username if self.author else (self.name or 'Anonymous')
        return f'Comment by {author_name} on {self.post.title}'
    
    def get_absolute_url(self):
        return f"{self.post.get_absolute_url()}#comment-{self.id}"
    
    def get_replies(self):
        """Get all active replies to this comment"""
        return self.replies.filter(active=True, is_approved=True)
    
    def get_reply_count(self):
        """Get count of active replies"""
        return self.replies.filter(active=True, is_approved=True).count()
    
    @property
    def is_parent(self):
        """Check if comment is a parent comment (no parent)"""
        return self.parent is None
    
    def approve(self, moderator=None):
        """Approve comment"""
        self.is_approved = True
        self.moderated_by = moderator
        self.moderated_at = timezone.now()
        self.save()
    
    def disapprove(self, moderator=None):
        """Disapprove comment"""
        self.is_approved = False
        self.moderated_by = moderator
        self.moderated_at = timezone.now()
        self.save()

class CommentVote(models.Model):
    """Model for comment likes/dislikes"""
    VOTE_CHOICES = (
        (1, 'Upvote'),
        (-1, 'Downvote'),
    )
    
    comment = models.ForeignKey(Comment, on_delete=models.CASCADE, related_name='votes')
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    vote = models.SmallIntegerField(choices=VOTE_CHOICES)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ['comment', 'user']
    
    def __str__(self):
        return f"{self.user.username} voted {self.get_vote_display()} on comment {self.comment.id}"

class CommentReport(models.Model):
    """Model for reporting inappropriate comments"""
    REPORT_REASONS = (
        ('spam', 'Spam'),
        ('harassment', 'Harassment'),
        ('hate_speech', 'Hate Speech'),
        ('inappropriate', 'Inappropriate Content'),
        ('other', 'Other'),
    )
    
    comment = models.ForeignKey(Comment, on_delete=models.CASCADE, related_name='reports')
    reporter = models.ForeignKey(User, on_delete=models.CASCADE)
    reason = models.CharField(max_length=20, choices=REPORT_REASONS)
    details = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    resolved = models.BooleanField(default=False)
    resolved_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='resolved_reports')
    resolved_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        unique_together = ['comment', 'reporter']
    
    def __str__(self):
        return f"Report on comment {self.comment.id} by {self.reporter.username}"