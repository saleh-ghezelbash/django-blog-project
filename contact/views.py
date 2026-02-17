from django.shortcuts import render, redirect
from django.contrib import messages
from django.core.mail import send_mail, EmailMessage
from django.conf import settings
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_protect
from django.views.decorators.http import require_POST
from django.utils import timezone
import json

from .models import ContactMessage, ContactInfo
from .forms import ContactForm

def get_client_ip(request):
    """Get client IP address"""
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip

def contact_us(request):
    """Contact us page"""
    contact_info = ContactInfo.get_info()
    form = ContactForm()
    
    context = {
        'contact_info': contact_info,
        'form': form,
        'recaptcha_enabled': contact_info.enable_recaptcha,
        'recaptcha_site_key': contact_info.recaptcha_site_key if contact_info.enable_recaptcha else None,
    }
    
    return render(request, 'contact/contact_us.html', context)

@csrf_protect
@require_POST
def contact_submit(request):
    """Handle contact form submission"""
    contact_info = ContactInfo.get_info()
    form = ContactForm(request.POST)
    
    if form.is_valid():
        # Save the message
        contact_message = form.save(commit=False)
        contact_message.ip_address = get_client_ip(request)
        contact_message.user_agent = request.META.get('HTTP_USER_AGENT', '')
        
        # Handle custom subject for "other"
        if contact_message.subject == 'other' and request.POST.get('custom_subject'):
            contact_message.custom_subject = request.POST.get('custom_subject')
        
        contact_message.save()
        
        # Send email notification to admin
        send_admin_notification(contact_message, contact_info)
        
        # Send auto-reply to user
        if contact_info.send_auto_reply:
            send_auto_reply(contact_message, contact_info)
        
        # Success message
        messages.success(request, 'Thank you for contacting us! We will get back to you soon.')
        
        # Check if AJAX request
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({
                'success': True,
                'message': 'Thank you for contacting us! We will get back to you soon.'
            })
        
        return redirect('contact_us')
    else:
        # Form is invalid
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({
                'success': False,
                'errors': form.errors
            }, status=400)
        
        # For regular form submission, show errors
        for field, errors in form.errors.items():
            for error in errors:
                messages.error(request, f"{field}: {error}")
        
        return render(request, 'contact/contact_us.html', {
            'form': form,
            'contact_info': contact_info,
        })

def send_admin_notification(message, contact_info):
    """Send email notification to admin"""
    try:
        subject = f"New Contact Message: {message.get_subject_display()}"
        email_body = f"""
        New contact message received:
        
        Name: {message.name}
        Email: {message.email}
        Phone: {message.phone or 'Not provided'}
        Subject: {message.get_subject_display()}
        Message: {message.message}
        
        Received at: {message.created_at}
        IP Address: {message.ip_address}
        """
        
        send_mail(
            subject=subject,
            message=email_body,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[contact_info.notification_email],
            fail_silently=True,
        )
    except Exception as e:
        print(f"Failed to send admin notification: {e}")

def send_auto_reply(message, contact_info):
    """Send auto-reply to user"""
    try:
        subject = contact_info.auto_reply_subject
        email_body = f"""
        Dear {message.name},
        
        {contact_info.auto_reply_message}
        
        We have received your message with the following details:
        
        Subject: {message.get_subject_display()}
        Message: {message.message}
        Received: {message.created_at.strftime('%B %d, %Y at %I:%M %p')}
        
        Our team will review your message and get back to you within 24-48 hours.
        
        Best regards,
        Blogzine Team
        """
        
        send_mail(
            subject=subject,
            message=email_body,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[message.email],
            fail_silently=True,
        )
    except Exception as e:
        print(f"Failed to send auto-reply: {e}")

def contact_success(request):
    """Contact form success page"""
    return render(request, 'contact/contact_success.html')
