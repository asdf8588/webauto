# -*- coding: utf-8 -*-
"""
测试任务模型
- 管理测试执行任务
- 记录执行历史和状态
"""
from django.db import models
import uuid
import json


class TestTask(models.Model):
    """测试执行任务"""
    
    # 任务类型
    TASK_TYPE_CHOICES = (
        ('single', '单个用例'),
        ('batch', '批量用例'),
        ('suite', '套件执行'),
        ('all', '全部执行'),
    )
    
    # 执行状态
    STATUS_CHOICES = (
        ('pending', '等待中'),
        ('running', '运行中'),
        ('completed', '已完成'),
        ('failed', '失败'),
        ('cancelled', '已取消'),
        ('timeout', '超时'),
    )
    
    # 基本信息
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField('任务名称', max_length=200)
    description = models.TextField('描述', blank=True, default='')
    
    # 任务配置
    task_type = models.CharField('任务类型', max_length=20, choices=TASK_TYPE_CHOICES, default='batch')
    status = models.CharField('状态', max_length=20, choices=STATUS_CHOICES, default='pending')
    
    # 关联数据（JSON 存储灵活配置）
    config = models.JSONField('执行配置', default=dict, blank=True)
    """
    config 结构示例:
    {
        "test_ids": [1, 2, 3],           // 用例ID列表
        "suite_id": null,                 // 套件ID（如果是套件执行）
        "markers": ["smoke"],             // pytest 标记
        "parallel": true,                // 是否并行
        "workers": 2,                     // 并行数
        "browser_type": "chromium",       // 浏览器类型
        "headed": false,                  // 是否有头模式
        "timeout": 3600,                  // 超时时间(秒)
        "extra_args": [],                 // 额外 pytest 参数
    }
    """
    
    # 执行结果统计
    result_summary = models.JSONField('结果摘要', default=dict, blank=True)
    """
    result_summary 结构:
    {
        "total": 50,
        "passed": 45,
        "failed": 3,
        "skipped": 2,
        "broken": 0,
        "duration": 120.5,               // 执行时长(秒)
        "pass_rate": 90.0,
    }
    """
    
    # 报告路径
    allure_report_path = models.CharField('Allure报告路径', max_length=500, blank=True, default='')
    trace_files = models.JSONField('Trace文件列表', default=list, blank=True)
    
    # 进程管理
    pid = models.IntegerField('进程PID', null=True, blank=True)
    started_at = models.DateTimeField('开始时间', null=True, blank=True)
    completed_at = models.DateTimeField('完成时间', null=True, blank=True)
    
    # 定时任务配置
    is_scheduled = models.BooleanField('定时任务', default=False)
    cron_expression = models.CharField('Cron表达式', max_length=100, blank=True, default='')
    next_run_time = models.DateTimeField('下次执行时间', null=True, blank=True)
    
    # 时间戳
    created_at = models.DateTimeField('创建时间', auto_now_add=True)
    updated_at = models.DateTimeField('更新时间', auto_now=True)
    created_by = models.CharField('创建者', max_length=50, default='system')
    
    class Meta:
        db_table = 'test_tasks'
        ordering = ['-created_at']
        verbose_name = '测试任务'
        verbose_name_plural = '测试任务'
        
    def __str__(self):
        return f"[{self.get_status_display()}] {self.name}"
    
    @property
    def duration(self):
        """计算执行时长"""
        if self.started_at and self.completed_at:
            return (self.completed_at - self.started_at).total_seconds()
        return None
    
    @property
    def pass_rate(self):
        """计算通过率"""
        summary = self.result_summary or {}
        total = summary.get('total', 0)
        passed = summary.get('passed', 0)
        if total > 0:
            return round(passed / total * 100, 1)
        return 0
    
    def get_allure_url(self, request=None):
        """获取 Allure 报告访问 URL"""
        if self.allure_report_path:
            from django.conf import settings
            return f"/api/reports/allure/{self.id}/"
        return None


class TaskLog(models.Model):
    """任务执行日志 - 实时记录输出"""
    
    LOG_LEVELS = (
        ('INFO', 'INFO'),
        ('DEBUG', 'DEBUG'),
        ('WARNING', 'WARNING'),
        ('ERROR', 'ERROR'),
    )
    
    id = models.BigAutoField(primary_key=True)
    task = models.ForeignKey(TestTask, on_delete=models.CASCADE, related_name='logs')
    level = models.CharField('日志级别', max_length=10, choices=LOG_LEVELS, default='INFO')
    message = models.TextField('日志内容')
    timestamp = models.DateTimeField('时间戳', auto_now_add=True)
    
    class Meta:
        db_table = 'task_logs'
        ordering = ['timestamp']
        verbose_name = '任务日志'
        verbose_name_plural = '任务日志'
        
    def __str__(self):
        return f"[{self.level}] {self.message[:50]}"
