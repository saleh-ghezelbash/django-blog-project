from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from django.utils import timezone
from .models import ContactMessage, ContactInfo

@admin.register(ContactMessage)
class ContactMessageAdmin(admin.ModelAdmin):
    list_display = ['name', 'email', 'subject_display', 'created_at', 'status', 'ip_address', 'action_buttons']
    list_filter = ['status', 'subject', 'created_at']
    search_fields = ['name', 'email', 'message']
    readonly_fields = ['ip_address', 'user_agent', 'created_at', 'read_at', 'replied_at', 'archived_at']
    
    # Define actions as a list of function names (NOT a method named 'actions')
    actions_list = ['mark_as_read', 'mark_as_replied', 'mark_as_archived']
    
    fieldsets = (
        ('Contact Information', {
            'fields': ('name', 'email', 'phone', 'subject', 'custom_subject')
        }),
        ('Message', {
            'fields': ('message',)
        }),
        ('Status', {
            'fields': ('status', 'read_at', 'replied_at', 'archived_at')
        }),
        ('Response', {
            'fields': ('response', 'responded_by')
        }),
        ('Technical Details', {
            'fields': ('ip_address', 'user_agent', 'created_at'),
            'classes': ('collapse',)
        }),
    )
    
    def subject_display(self, obj):
        if obj.subject == 'other' and obj.custom_subject:
            return f"{obj.get_subject_display()} - {obj.custom_subject}"
        return obj.get_subject_display()
    subject_display.short_description = 'Subject'
    
    def action_buttons(self, obj):
        buttons = []
        if obj.status != 'read':
            buttons.append(f'<a class="button" href="{reverse("admin:contact_contactmessage_change", args=[obj.id])}?mark=read" style="margin-right: 5px;">Mark Read</a>')
        if obj.status != 'replied':
            buttons.append(f'<a class="button" href="{reverse("admin:contact_contactmessage_change", args=[obj.id])}?mark=replied" style="margin-right: 5px;">Mark Replied</a>')
        if obj.status != 'archived':
            buttons.append(f'<a class="button" href="{reverse("admin:contact_contactmessage_change", args=[obj.id])}?mark=archived" style="margin-right: 5px;">Archive</a>')
        
        buttons.append(f'<a class="button" href="mailto:{obj.email}?subject=Re: {obj.get_subject_display()}" style="background-color: #28a745; color: white; padding: 5px 10px; text-decoration: none; border-radius: 3px;">Reply via Email</a>')
        
        return format_html('&nbsp;'.join(buttons))
    action_buttons.short_description = 'Actions'
    
    def mark_as_read(self, request, queryset):
        for obj in queryset:
            obj.mark_as_read()
        self.message_user(request, f'{queryset.count()} messages marked as read.')
    mark_as_read.short_description = "Mark selected as read"
    
    def mark_as_replied(self, request, queryset):
        for obj in queryset:
            obj.mark_as_replied()
        self.message_user(request, f'{queryset.count()} messages marked as replied.')
    mark_as_replied.short_description = "Mark selected as replied"
    
    def mark_as_archived(self, request, queryset):
        for obj in queryset:
            obj.mark_as_archived()
        self.message_user(request, f'{queryset.count()} messages archived.')
    mark_as_archived.short_description = "Archive selected"
    
    def get_actions(self, request):
        """Override get_actions to use our actions_list"""
        actions = super().get_actions(request)
        # Add our custom actions
        for action in self.actions_list:
            if hasattr(self, action):
                actions[action] = (getattr(self, action), action, getattr(self, action).short_description)
        return actions
    
    def save_model(self, request, obj, form, change):
        if 'mark' in request.GET:
            if request.GET['mark'] == 'read':
                obj.mark_as_read()
            elif request.GET['mark'] == 'replied':
                obj.mark_as_replied()
            elif request.GET['mark'] == 'archived':
                obj.mark_as_archived()
        super().save_model(request, obj, form, change)

@admin.register(ContactInfo)
class ContactInfoAdmin(admin.ModelAdmin):
    fieldsets = (
        ('Advertisement Contact', {
            'fields': ('advertise_address', 'advertise_phone', 'advertise_email', 'advertise_hours')
        }),
        ('General Contact', {
            'fields': ('general_address', 'general_phone', 'general_email', 'general_hours')
        }),
        ('Map Settings', {
            'fields': ('map_embed_url',)
        }),
        ('reCAPTCHA Settings', {
            'fields': ('enable_recaptcha', 'recaptcha_site_key', 'recaptcha_secret_key')
        }),
        ('Email Settings', {
            'fields': ('notification_email', 'send_auto_reply', 'auto_reply_subject', 'auto_reply_message')
        }),
    )
    
    def has_add_permission(self, request):
        # Only allow one instance
        return not ContactInfo.objects.exists()
    
    def has_delete_permission(self, request, obj=None):
        # Prevent deletion
        return False