from django import forms
from .models import ContactMessage

class ContactForm(forms.ModelForm):
    class Meta:
        model = ContactMessage
        fields = ['name', 'email', 'phone', 'subject', 'message']
        widgets = {
            'message': forms.Textarea(attrs={'rows': 6}),
        }
    
    def clean_email(self):
        email = self.cleaned_data.get('email')
        if email and '@' not in email:
            raise forms.ValidationError('Please enter a valid email address.')
        return email
    
    def clean_phone(self):
        phone = self.cleaned_data.get('phone')
        if phone and not phone.replace(' ', '').replace('-', '').replace('(', '').replace(')', '').isdigit():
            raise forms.ValidationError('Please enter a valid phone number.')
        return phone
    
    def clean_message(self):
        message = self.cleaned_data.get('message')
        if len(message.strip()) < 10:
            raise forms.ValidationError('Message must be at least 10 characters long.')
        return message