# certificates/urls.py
from django.contrib import admin
from django.urls import path, include
from certificates import views
from .views import IssueCertificateView

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/certificates/issue/', views.issue_certificate_view, name='issue_certificate'),
    path('api/certificates/verify/<str:cert_hash>/', views.verify_certificate_view, name='verify_certificate'),
    path('api/admin/login/', views.admin_login, name='admin_login'),
    path('issue/', IssueCertificateView.as_view(), name='issue-certificate'),
]
