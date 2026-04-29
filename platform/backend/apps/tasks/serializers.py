# -*- coding: utf-8 -*-
"""测试任务序列化器"""
from rest_framework import serializers
from .models import TestTask, TaskLog


class TestTaskSerializer(serializers.ModelSerializer):
    """测试任务序列化器"""
    type_display = serializers.CharField(source='get_task_type_display', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    duration = serializers.ReadOnlyField()
    pass_rate = serializers.ReadOnlyField()

    class Meta:
        model = TestTask
        fields = [
            'id', 'name', 'description', 'task_type', 'type_display',
            'status', 'status_display', 'config', 'result_summary',
            'allure_report_path', 'trace_files', 'pid',
            'started_at', 'completed_at', 'duration', 'pass_rate',
            'is_scheduled', 'cron_expression', 'next_run_time',
            'created_at', 'updated_at', 'created_by',
        ]
        read_only_fields = ['id', 'status', 'result_summary', 'duration', 'pass_rate',
                           'started_at', 'completed_at', 'pid', 'created_at']


class TaskLogSerializer(serializers.ModelSerializer):
    """任务日志序列化器"""

    class Meta:
        model = TaskLog
        fields = ['id', 'level', 'message', 'timestamp']


class TaskCreateSerializer(serializers.ModelSerializer):
    """创建任务的简化序列化器"""
    class Meta:
        model = TestTask
        fields = ['id', 'name', 'description', 'task_type', 'config', 
                  'is_scheduled', 'cron_expression']
