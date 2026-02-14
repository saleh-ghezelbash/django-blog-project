from django import forms
from django.core.validators import validate_email
from django.core.exceptions import ValidationError
from .models import Comment

class CommentForm(forms.ModelForm):
    class Meta:
        model = Comment
        fields = ['content', 'name', 'email', 'website', 'parent']
        widgets = {
            'content': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 4,
                'placeholder': 'Write your comment here...',
                'required': True,
            }),
            'name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Your name *',
            }),
            'email': forms.EmailInput(attrs={
                'class': 'form-control',
                'placeholder': 'Your email *',
            }),
            'website': forms.URLInput(attrs={
                'class': 'form-control',
                'placeholder': 'Your website (optional)',
            }),
            'parent': forms.HiddenInput(),
        }
    
    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        
        # If user is authenticated, hide name and email fields
        if self.user and self.user.is_authenticated:
            self.fields['name'].widget = forms.HiddenInput()
            self.fields['email'].widget = forms.HiddenInput()
            self.fields['name'].required = False
            self.fields['email'].required = False
    
    def clean_email(self):
        email = self.cleaned_data.get('email')
        if email and not self.user:
            try:
                validate_email(email)
            except ValidationError:
                raise forms.ValidationError('Please enter a valid email address.')
        return email
    
    def clean_name(self):
        name = self.cleaned_data.get('name')
        if not self.user and not name:
            raise forms.ValidationError('Name is required for anonymous comments.')
        return name
    
    def clean_content(self):
        content = self.cleaned_data.get('content')
        if len(content.strip()) < 3:
            raise forms.ValidationError('Comment must be at least 3 characters long.')
        if len(content) > 5000:
            raise forms.ValidationError('Comment must not exceed 5000 characters.')
        return content

class CommentReplyForm(forms.ModelForm):
    class Meta:
        model = Comment
        fields = ['content']
        widgets = {
            'content': forms.Textarea(attrs={
                'class': 'form-control reply-content',
                'rows': 3,
                'placeholder': 'Write your reply...',
            }),
        }
    
    def clean_content(self):
        content = self.cleaned_data.get('content')
        if len(content.strip()) < 3:
            raise forms.ValidationError('Reply must be at least 3 characters long.')
        return content