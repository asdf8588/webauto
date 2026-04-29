# -*- coding: utf-8 -*-
"""
测试任务执行 Views
- 创建和执行测试任务
- 查看实时日志
- 停止正在运行的任务
"""
import os
import sys
import subprocess
import threading
import time
import json
from datetime import datetime

from django.conf import settings
from django.views.decorators.csrf import csrf_exempt
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response

from .models import TestTask, TaskLog
from .serializers import TestTaskSerializer, TaskLogSerializer
from .executor import TestExecutor


class TestTaskViewSet(viewsets.ModelViewSet):
    """测试任务 ViewSet"""
    queryset = TestTask.objects.all()
    serializer_class = TestTaskSerializer
    
    @action(detail=True, methods=['post'])
    def execute(self, request, pk=None):
        """
        执行测试任务
        
        POST /api/tasks/{id}/execute/
        
        返回实时执行的流式日志
        """
        task = self.get_object()
        
        # 检查是否已在运行
        if task.status == 'running':
            return Response(
                {'error': '任务正在运行中'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # 重置任务状态
        task.status = 'pending'
        task.pid = None
        task.started_at = None
        task.completed_at = None
        task.result_summary = {}
        task.save(update_fields=['status', 'pid', 'started_at', 'completed_at', 'result_summary'])
        
        # 清除旧日志
        TaskLog.objects.filter(task=task).delete()
        
        # 异步执行测试
        executor = TestExecutor(task)
        thread = threading.Thread(target=executor.run, daemon=True)
        thread.start()
        
        return Response({
            'task_id': str(task.id),
            'status': 'running',
            'message': '任务已启动',
        })
    
    @action(detail=True, methods=['post'])
    def stop(self, request, pk=None):
        """停止正在运行的任务"""
        task = self.get_object()
        
        if task.status != 'running':
            return Response({'error': '任务未在运行'}, status=status.HTTP_400_BAD_REQUEST)
        
        if task.pid:
            try:
                # Windows 使用 taskkill
                if sys.platform == 'win32':
                    subprocess.run(['taskkill', '/F', '/PID', str(task.pid)], 
                                  capture_output=True, timeout=5)
                else:
                    import signal
                    os.kill(task.pid, signal.SIGTERM)
            except Exception as e:
                return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
        task.status = 'cancelled'
        task.completed_at = datetime.now()
        task.save(update_fields=['status', 'completed_at'])
        
        TaskLog.objects.create(task=task, level='WARNING', message='任务已被用户停止')
        
        return Response({'message': '任务已停止'})
    
    @action(detail=True, methods=['get'])
    def logs(self, request, pk=None):
        """获取任务执行日志（支持分页和实时）"""
        task = self.get_object()
        logs = task.logs.all().order_by('-timestamp')[:500]  # 最近500条
        
        serializer = TaskLogSerializer(logs, many=True)
        return Response(serializer.data)
    
    @action(detail=True, methods=['get'])
    def output(self, request, pk=None):
        """获取任务最新输出（用于实时刷新）"""
        task = self.get_object()
        recent_logs = task.logs.all().order_by('-timestamp')[:50]
        
        serializer = TaskLogSerializer(recent_logs, many=True)
        return Response({
            'status': task.status,
            'result_summary': task.result_summary,
            'logs': serializer.data,
            'started_at': task.started_at,
            'completed_at': task.completed_at,
        })

    @action(detail=False, methods=['get'])
    def running(self, request):
        """获取当前正在运行的任务"""
        running_tasks = TestTask.objects.filter(status='running').order_by('-started_at')
        serializer = TestTaskSerializer(running_tasks, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['post'])
    def run_quick(self, request):
        """
        快速执行 - 直接传入参数立即执行
        
        POST /api/tasks/run_quick/
        Body:
        {
            "test_ids": [1, 2, 3],      // 可选：指定用例
            "marker": "smoke",           // 可选：pytest 标记
            "suite_id": 1,              // 可选：套件ID
            "parallel": false,          // 是否并行
            "workers": 2,               // 并行数
            "name": "快速测试"          // 任务名称
        }
        """
        data = request.data.copy()
        data['name'] = data.get('name', f"快速测试_{datetime.now().strftime('%H:%M:%S')}")
        data['task_type'] = 'batch' if data.get('test_ids') else ('suite' if data.get('suite_id') else 'all')
        data['status'] = 'pending'
        
        serializer = self.get_serializer(data=data)
        if serializer.is_valid():
            task = serializer.save()
            
            # 自动开始执行
            executor = TestExecutor(task)
            thread = threading.Thread(target=executor.run, daemon=True)
            thread.start()
            
            return Response(TestTaskSerializer(task).data, status=status.HTTP_201_CREATED)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=False, methods=['get'])
    def history(self, request):
        """获取执行历史"""
        limit = int(request.query_params.get('limit', 20))
        tasks = TestTask.objects.exclude(status='pending').order_by('-completed_at', '-created_at')[:limit]
        serializer = TestTaskSerializer(tasks, many=True)
        return Response(serializer.data)
