# -*- coding: utf-8 -*-
"""
测试用例模型
- 管理所有 pytest 测试用例
- 支持从 webauto/tests 目录自动扫描导入
"""
from django.db import models
from django.utils import timezone
import os
import re
import ast


class TestCase(models.Model):
    """测试用例模型"""
    
    # 用例类型选择
    TYPE_CHOICES = (
        ('ui', 'UI 测试'),
        ('api', 'API 测试'),
        ('e2e', 'E2E 测试'),
    )
    
    # 优先级选择
    PRIORITY_CHOICES = (
        (0, 'P0 - 阻塞'),
        (1, 'P1 - 严重'),
        (2, 'P2 - 一般'),
        (3, 'P3 - 低'),
    )
    
    # 状态选择
    STATUS_CHOICES = (
        ('active', '启用'),
        ('inactive', '禁用'),
        ('deprecated', '已废弃'),
    )
    
    # 基本信息
    name = models.CharField('用例名称', max_length=200)
    module = models.CharField('所属模块', max_length=100)
    file_path = models.CharField('文件路径', max_length=500)  # YAML: 目录/文件.yaml, Pytest: 目录/文件.py
    test_id = models.CharField('测试ID/函数名', max_length=200)  # YAML: yaml_模块_功能_序号, Pytest: test_函数名
    
    # 分类信息
    case_type = models.CharField('用例类型', max_length=10, choices=TYPE_CHOICES, default='api')
    priority = models.IntegerField('优先级', choices=PRIORITY_CHOICES, default=2)
    tags = models.JSONField('标签', default=list, blank=True)  # ['smoke', 'regression']
    
    # 描述和文档
    description = models.TextField('描述', blank=True, default='')
    docstring = models.TextField('函数文档', blank=True, default='')
    
    # 执行配置
    timeout = models.IntegerField('超时时间(秒)', default=300)
    status = models.CharField('状态', max_length=20, choices=STATUS_CHOICES, default='active')
    
    # 时间戳
    created_at = models.DateTimeField('创建时间', auto_now_add=True)
    updated_at = models.DateTimeField('更新时间', auto_now=True)
    last_run_at = models.DateTimeField('最后运行时间', null=True, blank=True)
    
    class Meta:
        db_table = 'test_cases'
        ordering = ['-priority', 'module', 'name']
        verbose_name = '测试用例'
        verbose_name_plural = '测试用例'
        # file_path + test_id 复合唯一约束
        constraints = [
            models.UniqueConstraint(fields=['file_path', 'test_id'], name='unique_file_test')
        ]
        
    def __str__(self):
        return f"[{self.get_case_type_display()}] {self.name}"
    
    @property
    def full_path(self):
        """返回完整的 pytest 路径"""
        return f"{self.file_path}::{self.test_id}"
    
    @classmethod
    def scan_from_directory(cls, directory=None):
        """
        从 webauto/tests 目录自动扫描测试用例
        
        Args:
            directory: 测试目录路径，默认使用 settings.WEBAUTO_TESTS_DIR
            
        Returns:
            tuple: (created_count, updated_count)
        """
        from django.conf import settings
        import pathlib
        
        base_dir = pathlib.Path(directory or settings.WEBAUTO_TESTS_DIR)
        if not base_dir.exists():
            return 0, 0
            
        created_count = 0
        updated_count = 0
        
        # 遍历所有 test_*.py 文件
        for py_file in base_dir.rglob("test_*.py"):
            relative_path = py_file.relative_to(base_dir.parent)
            file_path_str = str(relative_path).replace('\\', '/')
            
            # 判断用例类型
            if '/ui/' in file_path_str:
                case_type = 'ui'
            elif '/api/' in file_path_str:
                case_type = 'api'
            else:
                case_type = 'e2e'
            
            # 解析 Python 文件，提取测试函数
            try:
                tree = ast.parse(py_file.read_text(encoding='utf-8'))
                
                for node in ast.walk(tree):
                    # 查找测试函数
                    if isinstance(node, ast.FunctionDef) and node.name.startswith('test_'):
                        test_id = node.name
                        
                        # 提取 docstring
                        docstring = ast.get_docstring(node) or ''
                        
                        # 从 docstring 或装饰器提取标签
                        tags = []
                        for decorator in node.decorator_list:
                            if isinstance(decorator, ast.Call):
                                if hasattr(decorator.func, 'attr') and decorator.func.attr == 'mark':
                                    for arg in decorator.args:
                                        if isinstance(arg, ast.Constant):
                                            tags.append(str(arg.value))
                        
                        # 模块名称：从文件路径提取
                        module = str(py_file.parent.relative_to(base_dir)).replace('/', '.')
                        
                        defaults = {
                            'file_path': file_path_str,
                            'test_id': test_id,
                            'case_type': case_type,
                            'module': module,
                            'docstring': docstring,
                            'tags': tags,
                        }
                        
                        # 创建或更新用例
                        obj, created = cls.objects.update_or_create(
                            file_path=file_path_str,
                            test_id=test_id,
                            defaults={
                                **defaults,
                                'name': docstring.split('\n')[0] if docstring else test_id,
                            }
                        )
                        
                        if created:
                            created_count += 1
                        else:
                            updated_count += 1
                            
            except SyntaxError as e:
                print(f"[扫描错误] 无法解析 {py_file}: {e}")
                continue
                
        return created_count, updated_count


class TestSuite(models.Model):
    """测试套件 - 用于组合多个用例批量执行"""
    
    name = models.CharField('套件名称', max_length=100)
    description = models.TextField('描述', blank=True, default='')
    cases = models.ManyToManyField(TestCase, related_name='suites', verbose_name='包含用例')
    
    # 配置
    parallel = models.BooleanField('并行执行', default=False)
    workers = models.IntegerField('并行数', default=2, null=True, blank=True)
    marker = models.CharField('pytest标记过滤', max_length=50, blank=True, default='')  # 如 smoke, regression
    
    # 时间戳
    created_at = models.DateTimeField('创建时间', auto_now_add=True)
    updated_at = models.DateTimeField('更新时间', auto_now=True)
    
    class Meta:
        db_table = 'test_suites'
        verbose_name = '测试套件'
        verbose_name_plural = '测试套件'
        
    def __str__(self):
        return self.name
    
    @property
    def case_count(self):
        return self.cases.count()
