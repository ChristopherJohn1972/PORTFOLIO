import time
import uuid
from collections import defaultdict
from django.conf import settings
from django.http import JsonResponse
from .models import SecurityLog


class SecurityLoggingMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response
        self._rate_limit_store = defaultdict(list)

    def __call__(self, request):
        if request.path.startswith('/static/') or request.path.startswith('/admin/'):
            return self.get_response(request)

        ip = self.get_client_ip(request)
        now = time.time()
        request_id = str(uuid.uuid4())
        user_agent = request.META.get('HTTP_USER_AGENT', '')[:500]
        referrer = request.META.get('HTTP_REFERER', '')[:500]

        # Store on request for views to use
        request._request_id = request_id
        request._client_ip = ip

        # Rate limiting for API endpoints
        if request.path.startswith('/api/') and request.method in ('POST', 'PUT', 'DELETE'):
            rate_limit = getattr(settings, 'RATE_LIMIT_PER_MINUTE', 10)
            window = 60

            self._rate_limit_store[ip] = [
                t for t in self._rate_limit_store[ip] if now - t < window
            ]

            if len(self._rate_limit_store[ip]) >= rate_limit:
                SecurityLog.objects.create(
                    event_type='rate_limit_exceeded',
                    severity='security',
                    endpoint=request.path,
                    http_method=request.method,
                    http_status=429,
                    result='blocked',
                    ip_address=ip,
                    user_agent=user_agent,
                    referrer=referrer,
                    request_id=request_id,
                    action_taken='Request rejected',
                    detail=f'Rate limit exceeded: {len(self._rate_limit_store[ip])} requests in {window}s (limit: {rate_limit})',
                )
                return JsonResponse({
                    'error': True,
                    'detail': 'Rate limit exceeded. Please try again later.',
                }, status=429)

            self._rate_limit_store[ip].append(now)

        response = self.get_response(request)

        # Log API events
        if request.path.startswith('/api/'):
            self._log_api_event(request, response, ip, user_agent, referrer, request_id)

        return response

    def _log_api_event(self, request, response, ip, user_agent, referrer, request_id):
        status_code = response.status_code
        method = request.method
        endpoint = request.path

        # Determine event type, result, severity based on status
        if status_code == 429:
            event_type = 'rate_limit_exceeded'
            result = 'blocked'
            severity = 'security'
            action = 'Request rate-limited'
        elif status_code == 401:
            event_type = 'unauthorized_access'
            result = 'blocked'
            severity = 'security'
            action = 'Authentication required'
        elif status_code == 403:
            event_type = 'forbidden_request'
            result = 'blocked'
            severity = 'security'
            action = 'Access denied'
        elif status_code == 404:
            event_type = 'invalid_endpoint'
            result = 'flagged'
            severity = 'warning'
            action = 'Endpoint not found'
        elif status_code == 400:
            event_type = 'validation_error'
            result = 'flagged'
            severity = 'warning'
            action = 'Validation failed'
        elif status_code >= 500:
            event_type = 'server_error'
            result = 'failed'
            severity = 'critical'
            action = 'Server error'
        elif method in ('POST', 'PUT', 'DELETE') and status_code < 400:
            # Successful mutations — log form submissions
            event_type = self._guess_form_event(endpoint)
            result = 'allowed'
            severity = 'info'
            action = 'Request processed'
        else:
            return  # Don't log routine GET requests from API

        SecurityLog.objects.create(
            event_type=event_type,
            severity=severity,
            endpoint=endpoint,
            http_method=method,
            http_status=status_code,
            result=result,
            ip_address=ip,
            user_agent=user_agent,
            referrer=referrer,
            request_id=request_id,
            action_taken=action,
            detail=f'{method} {endpoint} → {status_code}',
        )

    def _guess_form_event(self, endpoint):
        if 'contact' in endpoint:
            return 'contact_request'
        elif 'cv-request' in endpoint:
            return 'cv_request'
        elif 'project-links' in endpoint:
            return 'project_link_request'
        elif 'login' in endpoint:
            return 'admin_login'
        return 'failed_request'

    def get_client_ip(self, request):
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            return x_forwarded_for.split(',')[0].strip()
        return request.META.get('REMOTE_ADDR', '127.0.0.1')
