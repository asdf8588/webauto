# -*- coding: utf-8 -*-
"""
测试用例 API Views
- CRUD 操作
- 自动扫描导入
- 批量操作
"""
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.pagination import PageNumberPagination
from django.db import models

from .models import TestCase, TestSuite
from .serializers import TestCaseSerializer, TestSuiteSerializer


class StandardResultsSetPagination(PageNumberPagination):
    page_size = 20
    page_size_query_param = 'page_size'
    max_page_size = 100


class TestCaseViewSet(viewsets.ModelViewSet):
    """测试用例 ViewSet"""
    queryset = TestCase.objects.all()
    serializer_class = TestCaseSerializer
    pagination_class = StandardResultsSetPagination
    filterset_fields = ['case_type', 'status', 'priority', 'module']
    search_fields = ['name', 'file_path', 'test_id', 'description']
    ordering_fields = ['name', 'priority', 'created_at', 'last_run_at']
    ordering = ['-priority', '-updated_at']

    def get_queryset(self):
        queryset = TestCase.objects.all()
        
        # 按 type 过滤
        case_type = self.request.query_params.get('type')
        if case_type:
            queryset = queryset.filter(case_type=case_type)
            
        # 按状态过滤
        status_filter = self.request.query_params.get('status')
        if status_filter:
            queryset = queryset.filter(status=status_filter)
            
        # 按标签过滤
        tag = self.request.query_params.get('tag')
        if tag:
            queryset = queryset.filter(tags__contains=[tag])
            
        # 按模块过滤
        module = self.request.query_params.get('module')
        if module:
            queryset = queryset.filter(module__icontains=module)
            
        # 搜索
        search = self.request.query_params.get('search')
        if search:
            queryset = queryset.filter(
                models.Q(name__icontains=search) |
                models.Q(file_path__icontains=search) |
                models.Q(test_id__icontains=search)
            )
            
        return queryset.distinct()

    @action(detail=False, methods=['post'])
    def scan(self, request):
        """
        扫描 webauto/tests 或 tests_data 目录，自动导入测试用例
        
        POST /api/cases/testcases/scan/
        
        参数：
        - source: 'pytest' (默认) 或 'yaml'
        
        返回：
        {
            "created": 15,
            "updated": 5,
            "total": 20,
            "message": "扫描完成"
        }
        """
        from django.conf import settings
        source = request.data.get('source', 'all')  # all, pytest, yaml
        
        created = updated = 0
        
        # 扫描 pytest 测试文件
        if source in ('all', 'pytest'):
            c, u = TestCase.scan_from_directory()
            created += c
            updated += u
        
        # 扫描 YAML 测试用例
        if source in ('all', 'yaml'):
            from .yaml_scanner import scan_yaml_cases
            result = scan_yaml_cases(settings.WEBAUTO_TESTS_DATA_DIR)
            created += result['created']
            updated += result['updated']
        
        total = TestCase.objects.count()
        return Response({
            'created': created,
            'updated': updated,
            'total': total,
            'message': f'扫描完成：新增 {created} 条，更新 {updated} 条，共 {total} 条用例',
        })

    @action(detail=False, methods=['get'])
    def stats(self, request):
        """
        获取用例统计信息
        
        GET /api/cases/testcases/stats/
        """
        from django.db.models import Count
        
        # 总体统计
        total = TestCase.objects.count()
        active = TestCase.objects.filter(status='active').count()
        
        # 按类型统计
        type_stats = TestCase.objects.values('case_type').annotate(count=Count('id'))
        
        # 按优先级统计
        priority_stats = TestCase.objects.values('priority').annotate(count=Count('id'))
        
        # 按状态统计
        status_stats = TestCase.objects.values('status').annotate(count=Count('id'))
        
        # 模块列表
        modules = TestCase.objects.values_list('module', flat=True).distinct()
        
        # 标签列表
        all_tags = []
        for tc in TestCase.objects.exclude(tags=[]):
            all_tags.extend(tc.tags)
        tags = list(set(all_tags))
        
        return Response({
            'total': total,
            'active': active,
            'by_type': dict(type_stats),
            'by_priority': dict(priority_stats),
            'by_status': dict(status_stats),
            'modules': list(modules),
            'tags': tags,
        })

    @action(detail=True, methods=['post'])
    def toggle(self, request, pk=None):
        """切换用例启用/禁用状态"""
        testcase = self.get_object()
        new_status = 'inactive' if testcase.status == 'active' else 'active'
        testcase.status = new_status
        testcase.save(update_fields=['status'])
        return Response({'status': new_status, 'message': f'已{"启用" if new_status == "active" else "禁用"}'})

    @action(detail=False, methods=['post'])
    def batch_toggle(self, request):
        """批量切换状态"""
        ids = request.data.get('ids', [])
        action_type = request.data.get('action', 'toggle')  # enable, disable, toggle
        
        if not ids:
            return Response({'error': '请提供用例ID列表'}, status=status.HTTP_400_BAD_REQUEST)
        
        queryset = TestCase.objects.filter(id__in=ids)
        
        if action_type == 'enable':
            queryset.update(status='active')
        elif action_type == 'disable':
            queryset.update(status='inactive')
        elif action_type == 'toggle':
            for tc in queryset:
                new_status = 'inactive' if tc.status == 'active' else 'active'
                tc.status = new_status
                tc.save(update_fields=['status'])
        
        return Response({'message': f'已更新 {len(ids)} 条用例'})


class TestSuiteViewSet(viewsets.ModelViewSet):
    """测试套件 ViewSet - 管理测试套件"""
    queryset = TestSuite.objects.all().select_related()
    serializer_class = TestSuiteSerializer
    pagination_class = StandardResultsSetPagination

    @action(detail=True, methods=['get'])
    def cases(self, request, pk=None):
        """获取套件中的所有用例"""
        suite = self.get_object()
        cases = suite.cases.all()
        serializer = TestCaseSerializer(cases, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=['post'])
    def add_cases(self, request, pk=None):
        """向套件添加用例"""
        suite = self.get_object()
        case_ids = request.data.get('case_ids', [])
        cases = TestCase.objects.filter(id__in=case_ids)
        suite.cases.add(*cases)
        return Response({
            'message': f'已添加 {len(case_ids)} 个用例',
            'total_cases': suite.case_count
        })

    @action(detail=True, methods=['post'])
    def remove_cases(self, request, pk=None):
        """从套件移除用例"""
        suite = self.get_object()
        case_ids = request.data.get('case_ids', [])
        suite.cases.remove(*case_ids)
        return Response({
            'message': f'已移除 {len(case_ids)} 个用例',
            'total_cases': suite.case_count
        })
