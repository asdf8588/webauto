# -*- coding: utf-8 -*-
from django.contrib import admin
from .models import TestCase, TestSuite


@admin.register(TestCase)
class TestCaseAdmin(admin.ModelAdmin):
    list_display = ['name', 'case_type', 'priority', 'status', 'module', 'updated_at']
    list_filter = ['case_type', 'status', 'priority', 'module']
    search_fields = ['name', 'file_path', 'test_id']
    readonly_fields = ['created_at', 'updated_at', 'last_run_at']
    
    fieldsets = (
        ('基本信息', {
            'fields': ('name', 'module', 'file_path', 'test_id')
        }),
        ('分类信息', {
            'fields': ('case_type', 'priority', 'tags')
        }),
        ('文档描述', {
            'fields': ('description', 'docstring')
        }),
        ('执行配置', {
            'fields': ('timeout', 'status')
        }),
        ('时间戳', {
            'fields': ('created_at', 'updated_at', 'last_run_at'),
            'classes': ('collapse',)
        }),
    )


@admin.register(TestSuite)
class TestSuiteAdmin(admin.ModelAdmin):
    list_display = ['name', 'case_count', 'parallel', 'marker', 'updated_at']
    filter_horizontal = ['cases']
