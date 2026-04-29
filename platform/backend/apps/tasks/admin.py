# -*- coding: utf-8 -*-
from django.contrib import admin
from .models import TestTask, TaskLog


class TaskLogInline(admin.TabularInline):
    model = TaskLog
    extra = 0
    readonly_fields = ['level', 'message', 'timestamp']
    ordering = ['-timestamp']


@admin.register(TestTask)
class TestTaskAdmin(admin.ModelAdmin):
    list_display = ['id', 'name', 'task_type', 'status', 'pass_rate', 
                   'started_at', 'completed_at']
    list_filter = ['status', 'task_type', 'is_scheduled']
    search_fields = ['name', 'description']
    readonly_fields = ['id', 'pid', 'started_at', 'completed_at', 
                      'created_at', 'updated_at', 'duration', 'pass_rate']
    inlines = [TaskLogInline]
    
    fieldsets = (
        ('基本信息', {
            'fields': ('id', 'name', 'description')
        }),
        ('任务配置', {
            'fields': ('task_type', 'config')
        }),
        ('执行结果', {
            'fields': ('status', 'result_summary', 'pass_rate', 'duration',
                      'allure_report_path', 'trace_files')
        }),
        ('时间信息', {
            'fields': ('pid', 'started_at', 'completed_at', 'created_at'),
            'classes': ('collapse',)
        }),
    )


@admin.register(TaskLog)
class TaskLogAdmin(admin.ModelAdmin):
    list_display = ['id', 'task', 'level', 'message', 'timestamp']
    list_filter = ['level']
    search_fields = ['message']
    ordering = ['-timestamp']
