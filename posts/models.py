from django.db import models
from django.urls import reverse
from django.utils import timezone
from django.utils.text import slugify
from django.contrib.auth import get_user_model
from ckeditor.fields import RichTextField
from taggit.managers import TaggableManager
from categories.models import Category

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
    
    content = RichTextField()
    excerpt = models.TextField(max_length=500, blank=True)
    
    featured_image = models.ImageField(upload_to='blog_images/', blank=True, null=True)
    
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='draft')
    published_date = models.DateTimeField(default=timezone.now)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    tags = TaggableManager(blank=True)
    
    view_count = models.PositiveIntegerField(default=0)
    
    class Meta:
        ordering = ('-published_date',)
        indexes = [
            models.Index(fields=['-published_date']),
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

class PostImage(models.Model):
    post = models.ForeignKey(Post, related_name='images', on_delete=models.CASCADE)
    image = models.ImageField(upload_to='post_images/')
    caption = models.CharField(max_length=200, blank=True)
    uploaded_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"Image for {self.post.title}"
