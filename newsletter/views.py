from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.http import HttpResponse
from .models import Subscriber, Newsletter

def newsletter_subscribe(request):
    """Subscribe to newsletter"""
    if request.method == 'POST':
        email = request.POST.get('email')
        if email:
            subscriber, created = Subscriber.objects.get_or_create(
                email=email,
                defaults={'is_active': True}
            )
            if not created and not subscriber.is_active:
                subscriber.is_active = True
                subscriber.save()
                messages.success(request, 'Your subscription has been reactivated!')
            elif created:
                messages.success(request, 'Thank you for subscribing to our newsletter!')
            else:
                messages.info(request, 'You are already subscribed to our newsletter.')
        else:
            messages.error(request, 'Please provide a valid email address.')
    
    return redirect(request.META.get('HTTP_REFERER', 'home'))

def newsletter_unsubscribe(request, email):
    """Unsubscribe from newsletter"""
    subscriber = get_object_or_404(Subscriber, email=email)
    subscriber.is_active = False
    subscriber.save()
    messages.success(request, 'You have been unsubscribed from our newsletter.')
    return redirect('home')