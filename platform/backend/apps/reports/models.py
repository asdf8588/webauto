# -*- coding: utf-8 -*-
"""
报告模型
- 管理 Allure 报告历史
- 管理 Playwright Trace 文件
"""
from django.db import models


class AllureReport(models.Model):
    """Allure 报告记录"""
    
    id = models.BigAutoField(primary_key=True)
    task = models.OneToOneField(
        'tasks.TestTask',
        on_delete=models.CASCADE,
        related_name='allure_report_record',
        null=True,
        blank=True,
        verbose_name='关联任务'
    )
    
    # 报告信息
    name = models.CharField('报告名称', max_length=200)
    report_dir = models.CharField('报告目录路径', max_length=500)
    
    # 结果统计（冗余存储，方便查询）
    total = models.IntegerField('总用例数', default=0)
    passed = models.IntegerField('通过', default=0)
    failed = models.IntegerField('失败', default=0)
    broken = models.IntegerField('损坏', default=0)
    skipped = models.IntegerField('跳过', default=0)
    pass_rate = models.FloatField('通过率', default=0.0)
    duration = models.FloatField('执行时长(秒)', default=0.0)
    
    # 时间戳
    created_at = models.DateTimeField('创建时间', auto_now_add=True)
    
    class Meta:
        db_table = 'allure_reports'
        ordering = ['-created_at']
        verbose_name = 'Allure报告'
        verbose_name_plural = 'Allure报告'
        
    def __str__(self):
        return f"[{self.pass_rate:.1f}%] {self.name}"


class TraceFile(models.Model):
    """Playwright Trace 文件记录"""
    
    id = models.BigAutoField(primary_key=True)
    filename = models.CharField('文件名', max_length=200)
    filepath = models.CharField('文件完整路径', max_length=500)
    filesize = models.BigIntegerField('文件大小(字节)', default=0)
    
    # 关联信息
    test_case = models.CharField('关联用例名', max_length=200, blank=True, default='')
    task = models.ForeignKey(
        'tasks.TestTask',
        on_delete=models.SET_NULL,
        related_name='traces',
        null=True,
        blank=True,
        verbose_name='关联任务'
    )
    
    # 时间戳
    created_at = models.DateTimeField('创建时间', auto_now_add=True)
    
    class Meta:
        db_table = 'trace_files'
        ordering = ['-created_at']
        verbose_name = 'Trace文件'
        verbose_name_plural = 'Trace文件'
        
    @property
    def filesize_display(self):
        """格式化文件大小显示"""
        size = self.filesize
        for unit in ['B', 'KB', 'MB', 'GB']:
            if size < 1024:
                return f"{size:.1f} {unit}"
            size /= 1024
        return f"{size:.1f} TB"
