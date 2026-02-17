from django.db import models
from django.utils import timezone

class ContactMessage(models.Model):
    SUBJECT_CHOICES = (
        ('general', 'General Inquiry'),
        ('advertise', 'Advertising / Sponsorship'),
        ('support', 'Technical Support'),
        ('feedback', 'Feedback / Suggestion'),
        ('other', 'Other'),
    )
    
    STATUS_CHOICES = (
        ('new', 'New'),
        ('read', 'Read'),
        ('replied', 'Replied'),
        ('archived', 'Archived'),
    )
    
    name = models.CharField(max_length=100)
    email = models.EmailField()
    phone = models.CharField(max_length=20, blank=True, null=True)
    subject = models.CharField(max_length=20, choices=SUBJECT_CHOICES, default='general')
    custom_subject = models.CharField(max_length=200, blank=True, null=True)  # For "other" subject
    message = models.TextField()
    
    # Meta data
    ip_address = models.GenericIPAddressField(blank=True, null=True)
    user_agent = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    # Status tracking
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='new')
    read_at = models.DateTimeField(blank=True, null=True)
    replied_at = models.DateTimeField(blank=True, null=True)
    archived_at = models.DateTimeField(blank=True, null=True)
    
    # Response tracking
    response = models.TextField(blank=True, null=True)
    responded_by = models.ForeignKey('users.CustomUser', on_delete=models.SET_NULL, 
                                     null=True, blank=True, related_name='contact_responses')
    
    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Contact Message'
        verbose_name_plural = 'Contact Messages'
    
    def __str__(self):
        return f"{self.name} - {self.get_subject_display()}"
    
    def mark_as_read(self):
        self.status = 'read'
        self.read_at = timezone.now()
        self.save(update_fields=['status', 'read_at'])
    
    def mark_as_replied(self):
        self.status = 'replied'
        self.replied_at = timezone.now()
        self.save(update_fields=['status', 'replied_at'])
    
    def mark_as_archived(self):
        self.status = 'archived'
        self.archived_at = timezone.now()
        self.save(update_fields=['status', 'archived_at'])

class ContactInfo(models.Model):
    """Contact information for the website"""
    # Advertisement contact
    advertise_address = models.CharField(max_length=255, default="2492 Centennial NW, Acworth, GA, 30102")
    advertise_phone = models.CharField(max_length=50, default="(678) 324-1251 (Toll-free)")
    advertise_email = models.EmailField(default="advertise@example.com")
    advertise_hours = models.CharField(max_length=100, default="Monday to Saturday, 9:30 am to 6:00 pm")
    
    # General contact
    general_address = models.CharField(max_length=255, default="750 Sing Sing Rd, Horseheads, NY, 14845")
    general_phone = models.CharField(max_length=50, default="469-537-2410 (Toll-free)")
    general_email = models.EmailField(default="contact@example.com")
    general_hours = models.CharField(max_length=100, default="Monday to Saturday, 9:00 am to 5:30 pm")
    
    # Map
    map_embed_url = models.URLField(default="https://www.google.com/maps/embed?pb=!1m18!1m12!1m3!1d193595.15830869428!2d-74.119763973046!3d40.69766374874431!2m3!1f0!2f0!3f0!3m2!1i1024!2i768!4f13.1!3m3!1m2!1s0x89c24fa5d33f083b%3A0xc80b8f06e177fe62!2sNew%20York%2C%20NY%2C%20USA!5e0!3m2!1sen!2sin!4v1698912345678!5m2!1sen!2sin")
    
    # reCAPTCHA settings
    enable_recaptcha = models.BooleanField(default=False)
    recaptcha_site_key = models.CharField(max_length=100, blank=True, null=True)
    recaptcha_secret_key = models.CharField(max_length=100, blank=True, null=True)
    
    # Email settings
    notification_email = models.EmailField(default="admin@example.com")
    send_auto_reply = models.BooleanField(default=True)
    auto_reply_subject = models.CharField(max_length=200, default="Thank you for contacting us")
    auto_reply_message = models.TextField(default="Thank you for reaching out. We have received your message and will get back to you soon.")
    
    # Meta
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = 'Contact Information'
        verbose_name_plural = 'Contact Information'
    
    def __str__(self):
        return "Contact Information"
    
    @classmethod
    def get_info(cls):
        """Get or create contact info"""
        info, created = cls.objects.get_or_create(id=1)
        return info