# -*- coding: utf-8 -*-
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from rest_framework.decorators import api_view
from rest_framework.response import Response
from .views import TestCaseViewSet, TestSuiteViewSet
from .yaml_executor import YAMLCaseExecutor
from .api_views import (
    GenerateFromOpenAPIView,
    SaveOpenAPIToYAMLView,
    TracesAPIView,
    GenerateReportAPIView
)

router = DefaultRouter()
router.register(r'testcases', TestCaseViewSet, basename='testcase')
router.register(r'suites', TestSuiteViewSet, basename='testsuite')

# YAML API views
@api_view(['GET'])
def yaml_cases_list(request):
    """获取所有 YAML 用例"""
    executor = YAMLCaseExecutor()
    cases = executor.get_yaml_cases()
    return Response(cases)

@api_view(['POST'])
def run_yaml_tests(request):
    """执行所有 YAML 用例"""
    executor = YAMLCaseExecutor()
    results = executor.run_all()
    return Response({
        'total': len(results),
        'passed': len([r for r in results if r.get('status') == 'passed']),
        'failed': len([r for r in results if r.get('status') == 'failed']),
        'results': results
    })

urlpatterns = [
    # YAML API
    path('yaml-cases/', yaml_cases_list, name='yaml-cases-list'),
    path('run-yaml/', run_yaml_tests, name='run-yaml-tests'),
    
    # OpenAPI API
    path('generate-from-openapi/', GenerateFromOpenAPIView.as_view(), name='generate-from-openapi'),
    path('save-openapi-to-yaml/', SaveOpenAPIToYAMLView.as_view(), name='save-openapi-to-yaml'),
    
    # Trace API
    path('traces/', TracesAPIView.as_view(), name='traces'),
    
    # Report API
    path('generate-report/', GenerateReportAPIView.as_view(), name='generate-report'),
    
    # Router URLs
    path('', include(router.urls)),
]
