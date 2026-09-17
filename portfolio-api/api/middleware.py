import time
import uuid
from collections import defaultdict
from django.conf import settings
from django.http import JsonResponse
from .models import SecurityLog


def get_client_ip(request):
    for header in ('HTTP_X_FORWARDED_FOR', 'HTTP_X_REAL_IP', 'HTTP_X_CLIENT_IP'):
        forwarded = request.META.get(header)
        if forwarded:
            return forwarded.split(',')[0].strip()
    return request.META.get('REMOTE_ADDR', '127.0.0.1')


class SecurityLoggingMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response
        self._rate_limit_store = defaultdict(list)

    def __call__(self, request):
        if request.path.startswith('/static/') or request.path.startswith('/admin/') or request.path.startswith('/dashboard/') or request.path == '/favicon.ico':
            return self.get_response(request)

        if request.method == 'OPTIONS':
            return self.get_response(request)

        ip = get_client_ip(request)
        now = time.time()
        request_id = str(uuid.uuid4())
        user_agent = request.META.get('HTTP_USER_AGENT', '')[:500]
        referrer = request.META.get('HTTP_REFERER', '')[:500]

        request._request_id = request_id
        request._client_ip = ip

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

        if request.path.startswith('/api/'):
            self._log_api_event(request, response, ip, user_agent, referrer, request_id)

        return response

    def _log_api_event(self, request, response, ip, user_agent, referrer, request_id):
        status_code = response.status_code
        method = request.method
        endpoint = request.path

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
            event_type = self._classify_event(endpoint)
            result = 'flagged'
            severity = 'warning'
            action = 'Validation failed'
        elif status_code >= 500:
            event_type = 'server_error'
            result = 'failed'
            severity = 'critical'
            action = 'Server error'
        elif method in ('POST', 'PUT', 'DELETE') and status_code < 400:
            event_type = self._classify_event(endpoint)
            result = 'allowed'
            severity = 'info'
            action = 'Request processed'
        elif method == 'GET' and endpoint.startswith('/api/event/'):
            event_type = 'portfolio_event'
            result = 'allowed'
            severity = 'info'
            action = 'Event recorded'
        else:
            return

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

    def _classify_event(self, endpoint):
        if 'event' in endpoint:
            return 'portfolio_event'
        elif 'contact' in endpoint:
            return 'contact_request'
        elif 'cv-request' in endpoint:
            return 'cv_request'
        elif 'project-links' in endpoint:
            return 'project_link_request'
        elif 'login' in endpoint:
            return 'admin_login'
        return 'failed_request'
