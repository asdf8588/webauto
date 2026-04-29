# -*- coding: utf-8 -*-
"""重置数据库并扫描 YAML 用例"""
import os, sys
sys.path.insert(0, 'D:/pythonshiyan/webauto/platform/backend')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'test_platform.settings')

import django
django.setup()

from django.core.management import call_command

# 重新迁移所有数据库
print('开始数据库迁移...')
call_command('migrate', verbosity=1)
print('\n数据库迁移完成')

# 创建管理员用户
from django.contrib.auth.models import User
if not User.objects.filter(username='admin').exists():
    User.objects.create_superuser('admin', 'admin@example.com', 'admin123')
    print('管理员用户已创建: admin / admin123')
else:
    print('管理员用户已存在')

# 创建用例
from apps.cases.models import TestCase
from apps.cases.yaml_scanner import YamlTestScanner

scanner = YamlTestScanner('D:/pythonshiyan/webauto/tests_data')
created, updated = scanner.scan_all()
print(f'\nYAML用例扫描结果: created={created}, updated={updated}')
print(f'总用例数: {TestCase.objects.count()}')

# 按模块统计
from django.db.models import Count
print('\n按模块统计:')
for module in TestCase.objects.values('module').annotate(count=Count('id')):
    print(f"  {module['module']}: {module['count']} 条")

# 显示前5条用例
print('\n前5条用例:')
for tc in TestCase.objects.all()[:5]:
    print(f"  [{tc.module}] {tc.name} ({tc.test_id})")
