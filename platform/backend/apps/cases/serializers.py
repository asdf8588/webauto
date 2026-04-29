# -*- coding: utf-8 -*-
"""
测试用例序列化器
"""
from rest_framework import serializers
from .models import TestCase, TestSuite


class TestCaseSerializer(serializers.ModelSerializer):
    """测试用例序列化器"""
    full_path = serializers.ReadOnlyField()
    type_display = serializers.CharField(source='get_case_type_display', read_only=True)
    priority_display = serializers.CharField(source='get_priority_display', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    
    class Meta:
        model = TestCase
        fields = [
            'id', 'name', 'module', 'file_path', 'test_id', 'full_path',
            'case_type', 'type_display', 'priority', 'priority_display',
            'tags', 'description', 'docstring', 'timeout', 'status', 
            'status_display', 'created_at', 'updated_at', 'last_run_at',
        ]
        read_only_fields = ['created_at', 'updated_at', 'last_run_at']


class TestSuiteSerializer(serializers.ModelSerializer):
    """测试套件序列化器"""
    case_count = serializers.ReadOnlyField()
    cases = TestCaseSerializer(many=True, read_only=True)
    
    class Meta:
        model = TestSuite
        fields = [
            'id', 'name', 'description', 'cases', 'case_count',
            'parallel', 'workers', 'marker', 'created_at', 'updated_at',
        ]
        read_only_fields = ['created_at', 'updated_at']


class TestSuiteSimpleSerializer(serializers.ModelSerializer):
    """测试套件简化序列化器（用于下拉选择）"""
    case_count = serializers.ReadOnlyField()
    
    class Meta:
        model = TestSuite
        fields = ['id', 'name', 'case_count', 'marker', 'parallel']
