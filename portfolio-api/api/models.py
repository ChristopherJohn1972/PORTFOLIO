import uuid
from django.db import models


class ContactRequest(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('reviewed', 'Reviewed'),
        ('responded', 'Responded'),
        ('spam', 'Spam'),
    ]

    id = models.AutoField(primary_key=True)
    request_id = models.CharField(max_length=36, unique=True, default=uuid.uuid4)
    full_name = models.CharField(max_length=255)
    company = models.CharField(max_length=255)
    email = models.EmailField(max_length=254)
    opportunity_type = models.CharField(max_length=50)
    position = models.CharField(max_length=255, blank=True)
    message = models.TextField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(blank=True)
    honeypot_hit = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'contact_requests'
        ordering = ['-created_at']

    def __str__(self):
        return f"Contact: {self.full_name} ({self.company}) - {self.created_at}"


class CVRequest(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('sent', 'CV Sent'),
        ('declined', 'Declined'),
        ('spam', 'Spam'),
    ]

    id = models.AutoField(primary_key=True)
    request_id = models.CharField(max_length=36, unique=True, default=uuid.uuid4)
    full_name = models.CharField(max_length=255)
    company = models.CharField(max_length=255)
    email = models.EmailField(max_length=254)
    position = models.CharField(max_length=255)
    message = models.TextField(blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(blank=True)
    honeypot_hit = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'cv_requests'
        ordering = ['-created_at']

    def __str__(self):
        return f"CV: {self.full_name} ({self.company}) - {self.position}"


class ProjectLinkRequest(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('links_sent', 'Links Sent'),
        ('declined', 'Declined'),
        ('spam', 'Spam'),
    ]

    id = models.AutoField(primary_key=True)
    request_id = models.CharField(max_length=36, unique=True, default=uuid.uuid4)
    full_name = models.CharField(max_length=255)
    company = models.CharField(max_length=255)
    email = models.EmailField(max_length=254)
    projects = models.JSONField(default=list)
    message = models.TextField(blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(blank=True)
    honeypot_hit = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'project_link_requests'
        ordering = ['-created_at']

    def __str__(self):
        return f"Links: {self.full_name} ({self.company}) - {self.created_at}"


class SecurityLog(models.Model):
    EVENT_TYPES = [
        ('portfolio_visit', 'Portfolio Visit'),
        ('page_view', 'Page View'),
        ('project_view', 'Project View'),
        ('cv_request', 'CV Request'),
        ('contact_request', 'Contact Request'),
        ('project_link_request', 'Project Link Request'),
        ('admin_login', 'Admin Login'),
        ('admin_logout', 'Admin Logout'),
        ('validation_error', 'Validation Error'),
        ('failed_request', 'Failed Request'),
        ('unauthorized_access', 'Unauthorized Access'),
        ('forbidden_request', 'Forbidden Request'),
        ('invalid_endpoint', 'Invalid Endpoint'),
        ('rate_limit_exceeded', 'Rate Limit Exceeded'),
        ('suspicious_request', 'Suspicious Request'),
        ('blocked_request', 'Blocked Request'),
        ('honeypot_triggered', 'Honeypot Triggered'),
        ('file_upload_violation', 'File Upload Violation'),
        ('server_error', 'Server Error'),
    ]

    RESULT_CHOICES = [
        ('allowed', 'Allowed'),
        ('blocked', 'Blocked'),
        ('flagged', 'Flagged'),
        ('failed', 'Failed'),
    ]

    SEVERITY_CHOICES = [
        ('info', 'Info'),
        ('warning', 'Warning'),
        ('security', 'Security'),
        ('critical', 'Critical'),
    ]

    id = models.AutoField(primary_key=True)
    event_id = models.CharField(max_length=36, unique=True, default=uuid.uuid4)
    event_type = models.CharField(max_length=50, choices=EVENT_TYPES)
    severity = models.CharField(max_length=20, choices=SEVERITY_CHOICES, default='info')
    endpoint = models.CharField(max_length=500)
    http_method = models.CharField(max_length=10)
    http_status = models.SmallIntegerField(null=True, blank=True)
    result = models.CharField(max_length=20, choices=RESULT_CHOICES, default='allowed')
    ip_address = models.GenericIPAddressField()
    user_agent = models.TextField(blank=True)
    referrer = models.TextField(blank=True)
    request_id = models.CharField(max_length=36, blank=True)
    action_taken = models.CharField(max_length=100, blank=True)
    location = models.CharField(max_length=255, blank=True)
    detail = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'security_logs'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['event_type']),
            models.Index(fields=['result']),
            models.Index(fields=['severity']),
            models.Index(fields=['ip_address']),
            models.Index(fields=['created_at']),
        ]

    def __str__(self):
        return f"[{self.event_type}] {self.result} - {self.created_at}"


class AdminToken(models.Model):
    user = models.OneToOneField('auth.User', on_delete=models.CASCADE, related_name='admin_token')
    token = models.CharField(max_length=64, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'admin_tokens'

    def __str__(self):
        return f"Token for {self.user.username}"
