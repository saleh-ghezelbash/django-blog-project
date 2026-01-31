from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from categories.models import Category
from posts.models import Post
from taggit.models import Tag
import random
from django.utils import timezone
from datetime import timedelta

User = get_user_model()

class Command(BaseCommand):
    help = 'Create sample data for the blog'

    def handle(self, *args, **kwargs):
        self.stdout.write('Creating sample data...')
        
        # Create users
        users = []
        for i in range(5):
            user, created = User.objects.get_or_create(
                username=f'user{i}',
                defaults={
                    'email': f'user{i}@example.com',
                    'first_name': f'First{i}',
                    'last_name': f'Last{i}',
                    'bio': f'Bio for user {i}',
                }
            )
            if created:
                user.set_password('password123')
                user.save()
            users.append(user)
        
        # Create categories
        categories = []
        category_names = ['Technology', 'Science', 'Travel', 'Food', 'Lifestyle', 'Sports']
        for name in category_names:
            category, created = Category.objects.get_or_create(
                name=name,
                defaults={'description': f'Posts about {name.lower()}'}
            )
            categories.append(category)
        
        # Create tags
        tags = []
        tag_names = ['python', 'django', 'web', 'development', 'tutorial', 'beginners', 
                    'advanced', 'tips', 'tricks', 'how-to']
        for name in tag_names:
            tag, created = Tag.objects.get_or_create(name=name)
            tags.append(tag)
        
        # Create posts
        for i in range(20):
            post = Post.objects.create(
                title=f'Sample Post {i+1}',
                author=random.choice(users),
                category=random.choice(categories),
                content=f'<p>This is the content of sample post {i+1}. Lorem ipsum dolor sit amet.</p>' * 10,
                excerpt=f'This is a sample excerpt for post {i+1}',
                status='published',
                published_date=timezone.now() - timedelta(days=random.randint(0, 365))
            )
            
            # Add random tags
            post.tags.add(*random.sample(tags, random.randint(2, 5)))
            
            # Create view count
            post.view_count = random.randint(0, 1000)
            post.save()
        
        self.stdout.write(self.style.SUCCESS('Successfully created sample data!'))