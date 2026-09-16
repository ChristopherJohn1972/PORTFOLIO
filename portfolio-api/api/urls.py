from django.urls import path
from . import views

urlpatterns = [
    path('health/', views.HealthView.as_view(), name='health'),

    # Public form submission endpoints
    path('contact/', views.ContactSubmitView.as_view(), name='contact-submit'),
    path('cv-request/', views.CVRequestSubmitView.as_view(), name='cv-request-submit'),
    path('project-links/', views.ProjectLinkRequestSubmitView.as_view(), name='project-links-submit'),

    # Portfolio event logging (frontend → backend)
    path('event/', views.PortfolioEventView.as_view(), name='portfolio-event'),

    # Admin endpoints
    path('admin/login/', views.AdminLoginView.as_view(), name='admin-login'),
    path('admin/dashboard/', views.AdminDashboardDataView.as_view(), name='admin-dashboard'),
    path('admin/requests/', views.AdminRequestsView.as_view(), name='admin-requests'),
    path('admin/requests/<str:request_id>/', views.AdminUpdateRequestView.as_view(), name='admin-update-request'),
    path('admin/security-logs/', views.AdminSecurityLogsView.as_view(), name='admin-security-logs'),
]
