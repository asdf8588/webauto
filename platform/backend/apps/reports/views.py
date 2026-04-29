# -*- coding: utf-8 -*-
"""
报告查看 Views
- Allure 报告嵌入/代理
- Playwright Trace 文件列表和查看
- 报告历史管理
"""
import os
import json
import shutil
from pathlib import Path

from django.conf import settings
from django.http import HttpResponse, Http404, FileResponse
from django.views.decorators.csrf import csrf_exempt
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response

from .models import AllureReport, TraceFile


class ReportViewSet(viewsets.ViewSet):
    """报告相关 API（非标准 CRUD）"""

    @action(detail=False, methods=['get'])
    def list_reports(self, request):
        """
        获取所有可用的 Allure 报告列表
        
        GET /api/reports/list_reports/
        """
        reports = []
        
        # 从数据库获取已保存的报告记录
        for record in AllureReport.objects.all()[:20]:
            reports.append({
                'id': record.id,
                'name': record.name,
                'task_id': str(record.task.id) if record.task else None,
                'total': record.total,
                'passed': record.passed,
                'failed': record.failed,
                'pass_rate': record.pass_rate,
                'duration': record.duration,
                'created_at': record.created_at.isoformat(),
                'url': f'/api/reports/allure/{record.id}/' if record.id else None,
            })
        
        return Response(reports)

    @action(detail=False, methods=['get'])
    def latest_report(self, request):
        """获取最新报告的访问 URL"""
        report_dir = settings.WEBAUTO_ALLURE_REPORT
        
        if not report_dir.exists():
            return Response({'error': '暂无报告'}, status=status.HTTP_404_NOT_FOUND)
        
        # 检查是否有最新的任务报告
        from apps.tasks.models import TestTask
        latest_task = TestTask.objects.filter(
            allure_report_path__isnull=False,
            status__in=['completed', 'failed']
        ).order_by('-completed_at').first()
        
        if latest_task:
            return Response({
                'task_id': str(latest_task.id),
                'report_path': latest_task.allure_report_path,
                'result_summary': latest_task.result_summary,
                'pass_rate': latest_task.pass_rate,
            })
        
        return Response({
            'report_exists': True,
            'report_path': str(report_dir),
            'message': '有本地报告但无关联任务'
        })

    @action(detail=True, methods=['get'], url_path='allure/(?P<task_id>[^/.]+)')
    def allure(self, request, task_id=None):
        """
        代理 Allure 报告页面
        
        GET /api/reports/allure/{task_id}/
        返回 HTML 页面，内嵌 iframe 指向实际报告
        """
        try:
            from uuid import UUID
            from apps.tasks.models import TestTask
            
            task = TestTask.objects.get(id=UUID(task_id))
            report_path = task.allure_report_path or settings.WEBAUTO_ALLURE_REPORT
            
            report_index = Path(report_path) / 'index.html'
            
            if not report_index.exists():
                raise Http404("报告不存在")
                
            # 读取并修改 index.html，确保资源路径正确
            html_content = report_index.read_text(encoding='utf-8')
            
            return HttpResponse(html_content, content_type='text/html')
            
        except (ValueError, TestTask.DoesNotExist):
            # 如果没有指定任务ID，尝试返回默认报告
            report_index = settings.WEBAUTO_ALLURE_REPORT / 'index.html'
            if report_index.exists():
                html_content = report_index.read_text(encoding='utf-8')
                return HttpResponse(html_content, content_type='text/html')
            raise Http404("报告不存在")

    @action(detail=False, methods=['get'])
    def allure_data(self, request):
        """
        提供 Allure 报告数据文件访问
        
        GET /api/reports/allure_data/?path=data/some-file.json
        """
        file_path = request.GET.get('path', '')
        
        # 安全检查：防止目录穿越
        base_path = settings.WEBAUTO_ALLURE_REPORT
        full_path = base_path / file_path
        
        try:
            full_path.resolve().relative_to(base_path.resolve())
        except ValueError:
            return Response({'error': '非法路径'}, status=status.HTTP_400_BAD_REQUEST)
        
        if not full_path.exists():
            raise Http404(f"文件不存在: {file_path}")
        
        if full_path.suffix == '.json':
            data = json.loads(full_path.read_text(encoding='utf-8'))
            return Response(data)
        elif full_path.suffix in ('.png', '.jpg', '.gif'):
            return FileResponse(open(full_path, 'rb'), content_type=f'image/{full_path.suffix[1:]}')
        elif full_path.suffix in ('.txt', '.log'):
            return FileResponse(open(full_path, 'rb'), content_type='text/plain')
        else:
            return FileResponse(open(full_path, 'rb'))

    @action(detail=False, methods=['get'])
    def traces(self, request):
        """
        获取 Playwright Trace 文件列表
        
        GET /api/reports/traces/
        """
        trace_dir = settings.WEBAUTO_TRACE_DIR
        
        if not trace_dir.exists():
            return Response([])
        
        traces = []
        for f in sorted(trace_dir.glob("*.zip"), key=lambda x: x.stat().st_mtime, reverse=True)[:50]:
            traces.append({
                'filename': f.name,
                'filesize': f.stat().st_size,
                'filesize_display': self._format_size(f.stat().st_size),
                'modified_time': f.stat().st_mtime,
                'url': f'/api/reports/traces/{f.name}/view/',
                'download_url': f'/api/reports/traces/{f.name}/download/',
            })
        
        return Response(traces)

    @action(detail=True, methods=['get'], url_path='traces/(?P<filename>[^/]+)/download')
    def download_trace(self, request, filename=None):
        """下载 Trace 文件"""
        trace_path = settings.WEBAUTO_TRACE_DIR / filename
        
        if not trace_path.exists() or not trace_path.suffix == '.zip':
            raise Http404("文件不存在")
            
        response = FileResponse(open(trace_path, 'rb'), as_attachment=True)
        response['Content-Disposition'] = f'attachment; filename="{filename}"'
        return response

    @action(detail=False, methods=['get'])
    def dashboard_stats(self, request):
        """
        获取仪表盘统计数据
        
        GET /api/reports/dashboard_stats/
        """
        from apps.tasks.models import TestTask
        from apps.cases.models import TestCase
        from datetime import timedelta
        from django.utils import timezone
        
        now = timezone.now()
        today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
        week_ago = today_start - timedelta(days=7)
        
        # 用例统计
        total_cases = TestCase.objects.count()
        active_cases = TestCase.objects.filter(status='active').count()
        
        # 任务统计
        total_tasks = TestTask.objects.count()
        completed_tasks = TestTask.objects.filter(status='completed').count()
        failed_tasks = TestTask.objects.filter(status='failed').count()
        
        # 今日执行
        today_tasks = TestTask.objects.filter(started_at__gte=today_start).count()
        
        # 本周趋势
        weekly_stats = {}
        for i in range(7):
            day = (today_start - timedelta(days=i)).date()
            day_tasks = TestTask.objects.filter(
                started_at__date=day,
                status__in=['completed', 'failed']
            )
            day_passed = sum(t.result_summary.get('passed', 0) for t in day_tasks)
            day_failed = sum(t.result_summary.get('failed', 0) for t in day_tasks)
            weekly_stats[str(day)] = {'passed': day_passed, 'failed': day_failed}
        
        # 最近一次测试结果
        last_task = TestTask.objects.filter(
            status__in=['completed', 'failed']
        ).order_by('-completed_at').first()
        
        return Response({
            'cases': {
                'total': total_cases,
                'active': active_cases,
            },
            'tasks': {
                'total': total_tasks,
                'completed': completed_tasks,
                'failed': failed_tasks,
                'today': today_tasks,
            },
            'last_result': TestTaskSerializer(last_task).data if last_task else None,
            'weekly_trend': dict(reversed(list(weekly_stats.items()))),
        })

    @staticmethod
    def _format_size(size):
        """格式化文件大小"""
        for unit in ['B', 'KB', 'MB', 'GB']:
            if size < 1024:
                return f"{size:.1f} {unit}"
            size /= 1024
        return f"{size:.1f} TB"


def get_allure_proxy(request):
    """Allure 报告代理视图（用于 iframe 嵌入）"""
    report_dir = settings.WEBAUTO_ALLURE_REPORT
    
    if not report_dir.exists():
        return HttpResponse('<h1>暂无测试报告</h1><p>请先执行测试用例</p>', 
                           status=status.HTTP_200_OK)
    
    index_html = report_dir / 'index.html'
    if not index_html.exists():
        return HttpResponse('<h1>报告尚未生成</h1><p>请等待测试完成</p>',
                           status=status.HTTP_200_OK)
    
    # 读取报告内容
    content = index_html.read_text(encoding='utf-8')
    return HttpResponse(content)


# 需要导入序列化器
from apps.tasks.serializers import TestTaskSerializer
