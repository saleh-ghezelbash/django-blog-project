from django.db import models
from taggit.managers import TaggableManager

class Tag(models.Model):
    name = models.CharField(max_length=100, unique=True)
    slug = models.SlugField(max_length=100, unique=True)
    description = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return self.name
    
    class Meta:
        ordering = ['name']

# This is optional if you want to extend the taggit model
# For simple use, we'll use TaggableManager in Post model directly