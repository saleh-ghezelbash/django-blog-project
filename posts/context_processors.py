from categories.models import Category

def category_context(request):
    categories = Category.objects.all()[:10]
    return {'categories': categories}