from django.db import models
from django.urls import reverse
from django.utils import timezone
from django.utils.text import slugify
from django.contrib.auth import get_user_model
from ckeditor.fields import RichTextField
from taggit.managers import TaggableManager
from categories.models import Category
from django.db.models import Count

User = get_user_model()

class Post(models.Model):
    STATUS_CHOICES = (
        ('draft', 'Draft'),
        ('published', 'Published'),
    )
    
    title = models.CharField(max_length=200)
    slug = models.SlugField(max_length=200, unique_for_date='published_date')
    author = models.ForeignKey(User, on_delete=models.CASCADE, related_name='blog_posts')
    category = models.ForeignKey(Category, on_delete=models.SET_NULL, null=True, related_name='posts')
    
    excerpt = models.TextField(max_length=500, blank=True)
    content = RichTextField()
    
    featured_image = models.ImageField(upload_to='blog_images/', blank=True, null=True)
    
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='draft')
    published_date = models.DateTimeField(default=timezone.now)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    tags = TaggableManager(blank=True)
    
    view_count = models.PositiveIntegerField(default=0)
    is_sponsored = models.BooleanField(default=False)
    rating = models.DecimalField(max_digits=3, decimal_places=1, null=True, blank=True)
    
    class Meta:
        ordering = ('-published_date',)
        indexes = [
            models.Index(fields=['-published_date']),
            models.Index(fields=['is_sponsored']),
            models.Index(fields=['category']),
        ]
    
    def __str__(self):
        return self.title
    
    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.title)
        super().save(*args, **kwargs)
    
    def get_absolute_url(self):
        return reverse('post_detail', kwargs={
            'year': self.published_date.year,
            'month': self.published_date.month,
            'day': self.published_date.day,
            'slug': self.slug
        })
    
    def increment_view_count(self):
        self.view_count += 1
        self.save(update_fields=['view_count'])

    def get_read_time(self):
        """Calculate estimated reading time in minutes"""
        # Average reading speed: 200-250 words per minute
        word_count = len(self.content.split())
        reading_time = max(1, word_count // 200)  # At least 1 minute
        return reading_time
    
    def get_rating_display(self):
        """Display rating with stars"""
        if not self.rating:
            return 'Not rated'
        return f'{self.rating} / 10'

    def get_media_type(self):
        """Determine if post has video, audio, or gallery"""
        if hasattr(self, 'video') and self.video:
            return 'video'
        elif hasattr(self, 'audio') and self.audio:
            return 'audio'
        elif self.images.count() > 1:
            return 'gallery'
        return 'standard'
    
    # Like-related methods
    def likes_count(self):
        """Get total number of likes"""
        return self.likes.filter(is_like=True).count()
    
    def dislikes_count(self):
        """Get total number of dislikes"""
        return self.likes.filter(is_like=False).count()
    
    def total_votes(self):
        """Get total number of votes (likes + dislikes)"""
        return self.likes.count()
    
    def net_votes(self):
        """Get net votes (likes - dislikes)"""
        return self.likes_count() - self.dislikes_count()
    
    def user_vote(self, user):
        """Get a specific user's vote on this post"""
        if user.is_authenticated:
            try:
                vote = self.likes.get(user=user)
                return vote.is_like
            except PostLike.DoesNotExist:
                return None
        return None
    
    def like_percentage(self):
        """Get percentage of likes out of total votes"""
        total = self.total_votes()
        if total == 0:
            return 0
        return (self.likes_count() / total) * 100


class PostLike(models.Model):
    """Model for post likes/dislikes"""
    post = models.ForeignKey(Post, on_delete=models.CASCADE, related_name='likes')
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='post_likes')
    is_like = models.BooleanField(default=True)  # True for like, False for dislike
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        unique_together = ['post', 'user']  # One vote per user per post
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['post', 'user']),
            models.Index(fields=['is_like']),
        ]
    
    def __str__(self):
        vote_type = "Like" if self.is_like else "Dislike"
        return f"{self.user.username} {vote_type}d {self.post.title}"
    
    @classmethod
    def toggle_like(cls, post, user):
        """Toggle like status (like/dislike)"""
        vote, created = cls.objects.get_or_create(
            post=post,
            user=user,
            defaults={'is_like': True}
        )
        
        if not created:
            if vote.is_like:
                # If already liked, remove the vote
                vote.delete()
                return {'action': 'removed', 'is_like': None}
            else:
                # If disliked, change to like
                vote.is_like = True
                vote.save()
                return {'action': 'changed', 'is_like': True}
        
        return {'action': 'added', 'is_like': True}
    
    @classmethod
    def toggle_dislike(cls, post, user):
        """Toggle dislike status"""
        vote, created = cls.objects.get_or_create(
            post=post,
            user=user,
            defaults={'is_like': False}
        )
        
        if not created:
            if not vote.is_like:
                # If already disliked, remove the vote
                vote.delete()
                return {'action': 'removed', 'is_like': None}
            else:
                # If liked, change to dislike
                vote.is_like = False
                vote.save()
                return {'action': 'changed', 'is_like': False}
        
        return {'action': 'added', 'is_like': False}


class PostImage(models.Model):
    post = models.ForeignKey(Post, related_name='images', on_delete=models.CASCADE)
    image = models.ImageField(upload_to='post_images/')
    caption = models.CharField(max_length=200, blank=True)
    uploaded_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"Image for {self.post.title}"