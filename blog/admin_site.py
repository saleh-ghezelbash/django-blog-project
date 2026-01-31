from django.contrib.admin import AdminSite
from django.utils.translation import gettext_lazy as _

class BlogAdminSite(AdminSite):
    site_header = _('Blog Administration')
    site_title = _('Blog Admin')
    index_title = _('Welcome to Blog Administration')

admin_site = BlogAdminSite(name='blog_admin')