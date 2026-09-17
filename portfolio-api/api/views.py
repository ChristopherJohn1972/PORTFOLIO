import logging
import threading
import requests
from django.conf import settings
from django.contrib.auth import authenticate
from django.http import JsonResponse
from django.utils import timezone
from django.db.models import Q
from rest_framework import status
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import ContactRequest, CVRequest, ProjectLinkRequest, SecurityLog
from .serializers import (
    ContactRequestSerializer,
    CVRequestSerializer,
    ProjectLinkRequestSerializer,
)
from .authentication import get_or_create_token

logger = logging.getLogger('portfolio.api')


def _send_email_async(subject, body, receiver):
    api_key = getattr(settings, 'RESEND_API_KEY', '')
    from_email = getattr(settings, 'RESEND_FROM_EMAIL', 'onboarding@resend.dev')
    if not api_key or not receiver:
        return
    try:
        resp = requests.post(
            'https://api.resend.com/emails',
            headers={
                'Authorization': f'Bearer {api_key}',
                'Content-Type': 'application/json',
            },
            json={
                'from': f'Portfolio <{from_email}>',
                'to': [receiver],
                'subject': subject,
                'text': body,
            },
            timeout=10,
        )
        if resp.status_code >= 400:
            logger.error(f'Resend API error {resp.status_code}: {resp.text}')
        else:
            logger.info(f'Email sent to {receiver}: {subject}')
    except Exception as e:
        logger.error(f'Failed to send email via Resend: {e}')


class HealthView(APIView):
    permission_classes = [AllowAny]

    def get(self, request):
        return Response({'status': 'healthy', 'service': 'portfolio-api'})


class PortfolioEventView(APIView):
    permission_classes = [AllowAny]

    VALID_EVENTS = [
        'portfolio_visit', 'page_view', 'project_view',
        'cv_request', 'contact_request', 'project_link_request',
    ]

    def post(self, request):
        return self._log_event(request, request.data)

    def get(self, request):
        return self._log_event(request, request.query_params)

    def _log_event(self, request, data):
        event_type = data.get('event_type', '')
        if event_type not in self.VALID_EVENTS:
            return Response({'error': 'Invalid event type'}, status=400)

        ip = get_client_ip(request)
        user_agent = request.META.get('HTTP_USER_AGENT', '')[:500]
        referrer = request.META.get('HTTP_REFERER', '')[:500]
        request_id = getattr(request, '_request_id', '')
        detail = data.get('detail', '')
        endpoint = data.get('endpoint', '/')

        SecurityLog.objects.create(
            event_type=event_type,
            severity='info',
            endpoint=endpoint,
            http_method=request.method,
            http_status=200,
            result='allowed',
            ip_address=ip,
            user_agent=user_agent,
            referrer=referrer,
            request_id=request_id,
            action_taken='Recorded',
            detail=detail or event_type.replace('_', ' ').title(),
        )

        return Response({'success': True}, status=201)


class ContactSubmitView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = ContactRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        honeypot_hit = data.pop('honeypot_hit', False)

        contact = ContactRequest(
            full_name=data['full_name'],
            company=data['company'],
            email=data['email'],
            opportunity_type=data['opportunity_type'],
            position=data.get('position', ''),
            message=data['message'],
            ip_address=get_client_ip(request),
            user_agent=request.META.get('HTTP_USER_AGENT', '')[:500],
            honeypot_hit=honeypot_hit,
        )

        if honeypot_hit:
            contact.status = 'spam'
            contact.save()
            SecurityLog.objects.create(
                event_type='honeypot_triggered',
                severity='security',
                endpoint='/api/contact/',
                http_method='POST',
                http_status=200,
                result='blocked',
                ip_address=get_client_ip(request),
                user_agent=request.META.get('HTTP_USER_AGENT', '')[:500],
                referrer=request.META.get('HTTP_REFERER', '')[:500],
                request_id=str(contact.request_id),
                action_taken='Submission accepted (honeypot)',
                detail=f'Honeypot triggered by {data["email"]}',
            )
            # Return success to not reveal detection
            return Response({'success': True}, status=status.HTTP_200_OK)

        contact.save()

        # Send email notification (non-blocking)
        receiver = settings.CONTACT_RECEIVER_EMAIL
        if receiver:
            subject = f"Portfolio Contact: {contact.opportunity_type} — {contact.full_name}"
            body = (
                f"New Contact Message\n\n"
                f"Name: {contact.full_name}\n"
                f"Company: {contact.company}\n"
                f"Email: {contact.email}\n"
                f"Opportunity Type: {contact.opportunity_type}\n"
                f"Position: {contact.position}\n"
                f"Message:\n{contact.message}\n\n"
                f"Request ID: {contact.request_id}\n"
                f"IP: {contact.ip_address}\n"
                f"Time: {contact.created_at}\n"
            )
            threading.Thread(target=_send_email_async, args=(subject, body, receiver), daemon=True).start()

        logger.info(
            'Contact request received',
            extra={
                'request_id': str(contact.request_id),
                'email': contact.email,
                'ip': contact.ip_address,
            }
        )

        return Response({
            'success': True,
            'message': 'Message received successfully.',
        }, status=status.HTTP_201_CREATED)


class CVRequestSubmitView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = CVRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        honeypot_hit = data.pop('honeypot_hit', False)

        cv_req = CVRequest(
            full_name=data['full_name'],
            company=data['company'],
            email=data['email'],
            position=data['position'],
            message=data.get('message', ''),
            ip_address=get_client_ip(request),
            user_agent=request.META.get('HTTP_USER_AGENT', '')[:500],
            honeypot_hit=honeypot_hit,
        )

        if honeypot_hit:
            cv_req.status = 'spam'
            cv_req.save()
            SecurityLog.objects.create(
                event_type='honeypot_triggered',
                severity='security',
                endpoint='/api/cv-request/',
                http_method='POST',
                http_status=200,
                result='blocked',
                ip_address=get_client_ip(request),
                user_agent=request.META.get('HTTP_USER_AGENT', '')[:500],
                referrer=request.META.get('HTTP_REFERER', '')[:500],
                request_id=str(cv_req.request_id),
                action_taken='Submission accepted (honeypot)',
                detail=f'Honeypot triggered by {data["email"]}',
            )
            return Response({'success': True}, status=status.HTTP_200_OK)

        cv_req.save()

        # Send email notification (non-blocking)
        receiver = settings.CONTACT_RECEIVER_EMAIL
        if receiver:
            subject = f"Portfolio CV Request: {cv_req.position} — {cv_req.full_name}"
            body = (
                f"New CV Request\n\n"
                f"Name: {cv_req.full_name}\n"
                f"Company: {cv_req.company}\n"
                f"Email: {cv_req.email}\n"
                f"Position: {cv_req.position}\n"
                f"Message:\n{cv_req.message}\n\n"
                f"Request ID: {cv_req.request_id}\n"
                f"IP: {cv_req.ip_address}\n"
                f"Time: {cv_req.created_at}\n"
            )
            threading.Thread(target=_send_email_async, args=(subject, body, receiver), daemon=True).start()

        logger.info(
            'CV request received',
            extra={
                'request_id': str(cv_req.request_id),
                'email': cv_req.email,
                'ip': cv_req.ip_address,
            }
        )

        return Response({
            'success': True,
            'message': 'CV request received successfully.',
        }, status=status.HTTP_201_CREATED)


class ProjectLinkRequestSubmitView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = ProjectLinkRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        honeypot_hit = data.pop('honeypot_hit', False)

        proj_req = ProjectLinkRequest(
            full_name=data['full_name'],
            company=data['company'],
            email=data['email'],
            projects=data['projects'],
            message=data.get('message', ''),
            ip_address=get_client_ip(request),
            user_agent=request.META.get('HTTP_USER_AGENT', '')[:500],
            honeypot_hit=honeypot_hit,
        )

        if honeypot_hit:
            proj_req.status = 'spam'
            proj_req.save()
            SecurityLog.objects.create(
                event_type='honeypot_triggered',
                severity='security',
                endpoint='/api/project-links/',
                http_method='POST',
                http_status=200,
                result='blocked',
                ip_address=get_client_ip(request),
                user_agent=request.META.get('HTTP_USER_AGENT', '')[:500],
                referrer=request.META.get('HTTP_REFERER', '')[:500],
                request_id=str(proj_req.request_id),
                action_taken='Submission accepted (honeypot)',
                detail=f'Honeypot triggered by {data["email"]}',
            )
            return Response({'success': True}, status=status.HTTP_200_OK)

        proj_req.save()

        # Send email notification (non-blocking)
        receiver = settings.CONTACT_RECEIVER_EMAIL
        if receiver:
            projects_str = ', '.join(proj_req.projects)
            subject = f"Portfolio Link Request: {projects_str} — {proj_req.full_name}"
            body = (
                f"New Project Links Request\n\n"
                f"Name: {proj_req.full_name}\n"
                f"Company: {proj_req.company}\n"
                f"Email: {proj_req.email}\n"
                f"Projects: {projects_str}\n"
                f"Message:\n{proj_req.message}\n\n"
                f"Request ID: {proj_req.request_id}\n"
                f"IP: {proj_req.ip_address}\n"
                f"Time: {proj_req.created_at}\n"
            )
            threading.Thread(target=_send_email_async, args=(subject, body, receiver), daemon=True).start()

        logger.info(
            'Project link request received',
            extra={
                'request_id': str(proj_req.request_id),
                'email': proj_req.email,
                'ip': proj_req.ip_address,
            }
        )

        return Response({
            'success': True,
            'message': 'Project links request received successfully.',
        }, status=status.HTTP_201_CREATED)


# --- Admin Views ---

class AdminLoginView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        username = request.data.get('username', '')
        password = request.data.get('password', '')

        if not username or not password:
            return Response({
                'error': True,
                'detail': 'Username and password required.',
            }, status=status.HTTP_400_BAD_REQUEST)

        user = authenticate(username=username, password=password)

        if user is None:
            SecurityLog.objects.create(
                event_type='admin_login',
                severity='security',
                endpoint='/api/admin/login/',
                http_method='POST',
                http_status=401,
                result='blocked',
                ip_address=get_client_ip(request),
                user_agent=request.META.get('HTTP_USER_AGENT', '')[:500],
                referrer=request.META.get('HTTP_REFERER', '')[:500],
                request_id=getattr(request, '_request_id', ''),
                action_taken='Login rejected',
                detail=f'Failed login attempt for user: {username}',
            )
            return Response({
                'error': True,
                'detail': 'Invalid credentials.',
            }, status=status.HTTP_401_UNAUTHORIZED)

        if not user.is_staff:
            return Response({
                'error': True,
                'detail': 'Unauthorized.',
            }, status=status.HTTP_403_FORBIDDEN)

        token = get_or_create_token(user)

        SecurityLog.objects.create(
            event_type='admin_login',
            severity='info',
            endpoint='/api/admin/login/',
            http_method='POST',
            http_status=200,
            result='allowed',
            ip_address=get_client_ip(request),
            user_agent=request.META.get('HTTP_USER_AGENT', '')[:500],
            referrer=request.META.get('HTTP_REFERER', '')[:500],
            request_id=getattr(request, '_request_id', ''),
            action_taken='Login successful',
            detail=f'Successful login: {username}',
        )

        return Response({
            'token': token,
            'user': user.username,
        })


class AdminDashboardDataView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        if not request.user.is_staff:
            return Response({'error': True, 'detail': 'Forbidden'}, status=403)

        now = timezone.now()
        today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)

        # Security event counts
        all_events = SecurityLog.objects.all()
        today_events = all_events.filter(created_at__gte=today_start)

        total_events = all_events.count()
        today_visits = today_events.filter(event_type='portfolio_visit').count()
        security_events = all_events.filter(severity__in=['security', 'critical']).count()
        flagged_events = today_events.filter(result='flagged').count()
        blocked_events = today_events.filter(result='blocked').count()
        cv_requests = all_events.filter(event_type='cv_request').count()
        contact_requests = all_events.filter(event_type='contact_request').count()
        project_link_requests = all_events.filter(event_type='project_link_request').count()

        # Request counts
        contacts_today = ContactRequest.objects.filter(created_at__gte=today_start).count()
        cv_requests_today = CVRequest.objects.filter(created_at__gte=today_start).count()
        link_requests_today = ProjectLinkRequest.objects.filter(created_at__gte=today_start).count()
        total_contacts = ContactRequest.objects.count()
        total_cv = CVRequest.objects.count()
        total_links = ProjectLinkRequest.objects.count()

        # Recent security events (last 50)
        recent_events = all_events.all()[:50]
        recent_events_data = [self._serialize_event(e) for e in recent_events]

        # Recent requests
        recent_contacts = ContactRequest.objects.all()[:10]
        recent_contacts_data = [{
            'request_id': str(c.request_id),
            'full_name': c.full_name,
            'company': c.company,
            'email': c.email,
            'opportunity_type': c.opportunity_type,
            'status': c.status,
            'created_at': c.created_at.isoformat(),
        } for c in recent_contacts]

        recent_cvs = CVRequest.objects.all()[:10]
        recent_cvs_data = [{
            'request_id': str(c.request_id),
            'full_name': c.full_name,
            'company': c.company,
            'email': c.email,
            'position': c.position,
            'status': c.status,
            'created_at': c.created_at.isoformat(),
        } for c in recent_cvs]

        recent_links = ProjectLinkRequest.objects.all()[:10]
        recent_links_data = [{
            'request_id': str(l.request_id),
            'full_name': l.full_name,
            'company': l.company,
            'email': l.email,
            'projects': l.projects,
            'status': l.status,
            'created_at': l.created_at.isoformat(),
        } for l in recent_links]

        return Response({
            'summary': {
                'total_events': total_events,
                'today_visits': today_visits,
                'security_events': security_events,
                'flagged_events': flagged_events,
                'blocked_events': blocked_events,
                'cv_requests': cv_requests,
                'contact_requests': contact_requests,
                'project_link_requests': project_link_requests,
                'contacts_today': contacts_today,
                'cv_requests_today': cv_requests_today,
                'link_requests_today': link_requests_today,
                'total_contacts': total_contacts,
                'total_cv': total_cv,
                'total_links': total_links,
            },
            'recent_events': recent_events_data,
            'recent_contacts': recent_contacts_data,
            'recent_cvs': recent_cvs_data,
            'recent_links': recent_links_data,
        })

    def _serialize_event(self, e):
        return {
            'event_id': str(e.event_id),
            'event_type': e.event_type,
            'event_type_display': e.get_event_type_display(),
            'severity': e.severity,
            'severity_display': e.get_severity_display(),
            'endpoint': e.endpoint,
            'http_method': e.http_method,
            'http_status': e.http_status,
            'result': e.result,
            'result_display': e.get_result_display(),
            'ip_address': e.ip_address,
            'user_agent': e.user_agent,
            'referrer': e.referrer,
            'request_id': e.request_id,
            'action_taken': e.action_taken,
            'location': e.location,
            'detail': e.detail,
            'created_at': e.created_at.isoformat(),
        }


class AdminRequestsView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        if not request.user.is_staff:
            return Response({'error': True, 'detail': 'Forbidden'}, status=403)

        request_type = request.query_params.get('type', 'contacts')
        status_filter = request.query_params.get('status', '')
        page = int(request.query_params.get('page', 1))
        per_page = int(request.query_params.get('per_page', 20))

        if request_type == 'contacts':
            qs = ContactRequest.objects.all()
        elif request_type == 'cv':
            qs = CVRequest.objects.all()
        elif request_type == 'links':
            qs = ProjectLinkRequest.objects.all()
        else:
            return Response({'error': True, 'detail': 'Invalid type'}, status=400)

        if status_filter:
            qs = qs.filter(status=status_filter)

        total = qs.count()
        offset = (page - 1) * per_page
        items = qs[offset:offset + per_page]

        data = []
        for item in items:
            entry = {
                'request_id': str(item.request_id),
                'full_name': item.full_name,
                'company': item.company,
                'email': item.email,
                'status': item.status,
                'ip_address': item.ip_address,
                'created_at': item.created_at.isoformat(),
            }
            if request_type == 'contacts':
                entry['opportunity_type'] = item.opportunity_type
                entry['position'] = item.position
                entry['message'] = item.message
            elif request_type == 'cv':
                entry['position'] = item.position
                entry['message'] = item.message
            elif request_type == 'links':
                entry['projects'] = item.projects
                entry['message'] = item.message
            data.append(entry)

        return Response({
            'items': data,
            'total': total,
            'page': page,
            'per_page': per_page,
            'pages': (total + per_page - 1) // per_page,
        })


class AdminUpdateRequestView(APIView):
    permission_classes = [IsAuthenticated]

    def patch(self, request, request_id):
        if not request.user.is_staff:
            return Response({'error': True, 'detail': 'Forbidden'}, status=403)

        new_status = request.data.get('status', '')
        request_type = request.query_params.get('type', 'contacts')

        if request_type == 'contacts':
            model = ContactRequest
        elif request_type == 'cv':
            model = CVRequest
        elif request_type == 'links':
            model = ProjectLinkRequest
        else:
            return Response({'error': True, 'detail': 'Invalid type'}, status=400)

        try:
            item = model.objects.get(request_id=request_id)
        except model.DoesNotExist:
            return Response({'error': True, 'detail': 'Not found'}, status=404)

        valid_statuses = [c[0] for c in model.STATUS_CHOICES]
        if new_status not in valid_statuses:
            return Response({'error': True, 'detail': 'Invalid status'}, status=400)

        item.status = new_status
        item.save()

        return Response({'success': True, 'status': new_status})


class AdminSecurityLogsView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        if not request.user.is_staff:
            return Response({'error': True, 'detail': 'Forbidden'}, status=403)

        # Filters
        event_type = request.query_params.get('event_type', '')
        result = request.query_params.get('result', '')
        severity = request.query_params.get('severity', '')
        method = request.query_params.get('method', '')
        status_code = request.query_params.get('status', '')
        ip = request.query_params.get('ip', '')
        endpoint = request.query_params.get('endpoint', '')
        search = request.query_params.get('search', '')
        date_from = request.query_params.get('date_from', '')
        date_to = request.query_params.get('date_to', '')
        page = int(request.query_params.get('page', 1))
        per_page = int(request.query_params.get('per_page', 50))

        # Event detail
        event_id = request.query_params.get('event_id', '')
        if event_id:
            try:
                e = SecurityLog.objects.get(event_id=event_id)
                return Response({
                    'event_id': str(e.event_id),
                    'event_type': e.event_type,
                    'event_type_display': e.get_event_type_display(),
                    'severity': e.severity,
                    'severity_display': e.get_severity_display(),
                    'endpoint': e.endpoint,
                    'http_method': e.http_method,
                    'http_status': e.http_status,
                    'result': e.result,
                    'result_display': e.get_result_display(),
                    'ip_address': e.ip_address,
                    'user_agent': e.user_agent,
                    'referrer': e.referrer,
                    'request_id': e.request_id,
                    'action_taken': e.action_taken,
                    'location': e.location,
                    'detail': e.detail,
                    'created_at': e.created_at.isoformat(),
                })
            except SecurityLog.DoesNotExist:
                return Response({'error': 'Event not found'}, status=404)

        qs = SecurityLog.objects.all()

        if event_type:
            qs = qs.filter(event_type=event_type)
        if result:
            qs = qs.filter(result=result)
        if severity:
            qs = qs.filter(severity=severity)
        if method:
            qs = qs.filter(http_method__iexact=method)
        if status_code:
            qs = qs.filter(http_status=int(status_code))
        if ip:
            qs = qs.filter(ip_address__icontains=ip)
        if endpoint:
            qs = qs.filter(endpoint__icontains=endpoint)
        if date_from:
            qs = qs.filter(created_at__date__gte=date_from)
        if date_to:
            qs = qs.filter(created_at__date__lte=date_to)
        if search:
            qs = qs.filter(
                Q(request_id__icontains=search) |
                Q(ip_address__icontains=search) |
                Q(detail__icontains=search)
            )

        total = qs.count()
        offset = (page - 1) * per_page
        items = qs[offset:offset + per_page]

        data = [{
            'event_id': str(e.event_id),
            'event_type': e.event_type,
            'event_type_display': e.get_event_type_display(),
            'severity': e.severity,
            'severity_display': e.get_severity_display(),
            'endpoint': e.endpoint,
            'http_method': e.http_method,
            'http_status': e.http_status,
            'result': e.result,
            'result_display': e.get_result_display(),
            'ip_address': e.ip_address,
            'user_agent': e.user_agent,
            'referrer': e.referrer,
            'request_id': e.request_id,
            'action_taken': e.action_taken,
            'location': e.location,
            'detail': e.detail,
            'created_at': e.created_at.isoformat(),
        } for e in items]

        return Response({
            'items': data,
            'total': total,
            'page': page,
            'per_page': per_page,
            'pages': (total + per_page - 1) // per_page,
        })


def get_client_ip(request):
    for header in ('HTTP_X_FORWARDED_FOR', 'HTTP_X_REAL_IP', 'HTTP_X_CLIENT_IP'):
        forwarded = request.META.get(header)
        if forwarded:
            return forwarded.split(',')[0].strip()
    return request.META.get('REMOTE_ADDR', '127.0.0.1')
