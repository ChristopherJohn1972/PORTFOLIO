from django.contrib import admin
from .models import ContactRequest, CVRequest, ProjectLinkRequest, SecurityLog, AdminToken

admin.site.register(ContactRequest)
admin.site.register(CVRequest)
admin.site.register(ProjectLinkRequest)
admin.site.register(SecurityLog)
admin.site.register(AdminToken)
