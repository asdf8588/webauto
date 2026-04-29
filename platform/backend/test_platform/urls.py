# -*- coding: utf-8 -*-
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.views.generic import TemplateView

from apps.cases import views as case_views

urlpatterns = [
    # Home page
    path('', TemplateView.as_view(template_name='index.html'), name='home'),
    
    # API routes
    path('api/cases/', include('apps.cases.urls')),
    path('api/tasks/', include('apps.tasks.urls')),
    path('api/reports/', include('apps.reports.urls')),
    
    # Django Admin
    path('admin/', admin.site.urls),
    
    # Allure report proxy
    path('allure/', TemplateView.as_view(template_name='allure_proxy.html'), name='allure-proxy'),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT) + static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
