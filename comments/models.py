from django.db import models
from django.urls import reverse
from django.utils import timezone
from django.contrib.auth import get_user_model
from posts.models import Post

User = get_user_model()

class Comment(models.Model):
    post = models.ForeignKey(Post, on_delete=models.CASCADE, related_name='comments')
    author = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='comments')
    name = models.CharField(max_length=100, blank=True)  # For non-authenticated users
    email = models.EmailField(blank=True)  # For non-authenticated users
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    active = models.BooleanField(default=True)
    
    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['created_at']),
        ]
    
    def __str__(self):
        return f'Comment by {self.author.username if self.author else self.name} on {self.post.title}'
    
    def get_absolute_url(self):
        return reverse('post_detail', kwargs={
            'year': self.post.published_date.year,
            'month': self.post.published_date.month,
            'day': self.post.published_date.day,
            'slug': self.post.slug
        }) + f'#comment-{self.id}'