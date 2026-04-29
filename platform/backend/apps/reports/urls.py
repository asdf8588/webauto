# -*- coding: utf-8 -*-
from django.urls import path
from .views import ReportViewSet, get_allure_proxy

router_urls = [
    path('list-reports/', ReportViewSet.as_view({'get': 'list_reports'}), name='list_reports'),
    path('latest/', ReportViewSet.as_view({'get': 'latest_report'}), name='latest_report'),
    path('dashboard/', ReportViewSet.as_view({'get': 'dashboard_stats'}), name='dashboard'),
    path('traces/', ReportViewSet.as_view({'get': 'traces'}), name='traces_list'),
]

urlpatterns = [
    *router_urls,
    path('allure-data/', ReportViewSet.as_view({'get': 'allure_data'}), name='allure_data'),
]
