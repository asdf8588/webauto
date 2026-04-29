# -*- coding: utf-8 -*-
"""扫描 YAML 用例"""
import os, sys
sys.path.insert(0, 'D:/pythonshiyan/webauto/platform/backend')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'test_platform.settings')

import django
django.setup()

from apps.cases.models import TestCase
from apps.cases.yaml_scanner import YamlTestScanner

# 清空旧用例
TestCase.objects.all().delete()
print('已清空旧用例')

# 重新扫描
scanner = YamlTestScanner('D:/pythonshiyan/webauto/tests_data')
created, updated = scanner.scan_all()
print(f'扫描结果: created={created}, updated={updated}')
print(f'总用例数: {TestCase.objects.count()}')

# 按模块统计
from django.db.models import Count
print('\n按模块统计:')
for module in TestCase.objects.values('module').annotate(count=Count('id')):
    print(f"  {module['module']}: {module['count']} 条")
