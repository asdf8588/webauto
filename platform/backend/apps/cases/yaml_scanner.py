# -*- coding: utf-8 -*-
"""
YAML 测试用例扫描器
扫描 tests_data/ 目录下的所有 YAML 文件，导入到数据库
"""
import os
import yaml
import uuid
from pathlib import Path
from typing import Dict, List, Any, Tuple


class YamlTestScanner:
    """YAML 测试用例扫描器"""
    
    # 优先级映射
    PRIORITY_MAP = {
        'P0': 0,
        'P1': 1,
        'P2': 2,
        'P3': 3,
    }
    
    def __init__(self, tests_data_dir: str):
        """
        Args:
            tests_data_dir: tests_data 目录路径
        """
        self.tests_data_dir = Path(tests_data_dir)
        self._uuid_cache = {}  # 缓存每个用例的 UUID
    
    def scan_all(self) -> Tuple[int, int]:
        """
        扫描所有 YAML 文件
        
        Returns:
            tuple: (created_count, updated_count)
        """
        from .models import TestCase
        
        created_count = 0
        updated_count = 0
        
        # 遍历所有 YAML 文件
        for yaml_file in self.tests_data_dir.rglob("*.yaml"):
            relative_path = yaml_file.relative_to(self.tests_data_dir)
            file_path_str = str(relative_path).replace('\\', '/')
            
            try:
                cases = self._parse_yaml_file(yaml_file)
                for case_data in cases:
                    obj, created = self._import_case(case_data, file_path_str)
                    if created:
                        created_count += 1
                    else:
                        updated_count += 1
                        
            except Exception as e:
                print(f"[扫描错误] {yaml_file}: {e}")
                continue
        
        return created_count, updated_count
    
    def _parse_yaml_file(self, yaml_path: Path) -> List[Dict[str, Any]]:
        """解析 YAML 文件"""
        with open(yaml_path, 'r', encoding='utf-8') as f:
            data = yaml.safe_load(f)
        
        if not data:
            return []
        
        # 支持单个用例或用例列表
        if isinstance(data, dict):
            return [data]
        elif isinstance(data, list):
            return data
        return []
    
    def _import_case(self, case_data: Dict, file_path: str) -> Tuple:
        """导入单个用例到数据库"""
        from .models import TestCase
        
        case_id = case_data.get('case_id', '')
        name = case_data.get('name', '')
        module = case_data.get('module', 'common')
        priority_str = case_data.get('priority', 'P2')
        tags = case_data.get('tags', [])
        description = case_data.get('description', '')
        
        # 转换优先级
        priority = self.PRIORITY_MAP.get(priority_str, 2)
        
        # 构建 pytest 路径格式
        test_id = f"yaml_{case_id.replace('.', '_')}"
        
        # 将 YAML 数据序列化存储
        yaml_data = {
            'method': case_data.get('method', 'GET'),
            'url': case_data.get('url', ''),
            'body': case_data.get('body', {}),
            'expected': case_data.get('expected', {}),
            'setup': case_data.get('setup', []),
            'cleanup': case_data.get('cleanup', False),
            'requires_auth': case_data.get('requires_auth', False),
            'verify': case_data.get('verify', {}),
            'steps': case_data.get('steps', []),
        }
        
        defaults = {
            'name': name,
            'module': module,
            'test_id': test_id,
            'case_type': 'api',  # YAML 用例默认为 API 测试
            'priority': priority,
            'tags': tags,
            'description': description,
            'docstring': yaml_data,  # 存储完整的 YAML 数据
            'status': 'active',
        }
        
        # 使用 file_path + test_id 复合唯一键查找或创建
        obj, created = TestCase.objects.get_or_create(
            file_path=file_path,
            test_id=test_id,
            defaults=defaults
        )
        
        # 如果用例已存在，更新其他字段
        if not created:
            for key, value in defaults.items():
                setattr(obj, key, value)
            obj.save()
        
        return obj, created
    
    def get_yaml_content(self, file_path: str) -> List[Dict]:
        """获取指定 YAML 文件的内容"""
        full_path = self.tests_data_dir / file_path
        if not full_path.exists():
            return []
        return self._parse_yaml_file(full_path)


def scan_yaml_cases(tests_data_dir: str = None) -> Dict:
    """
    扫描 YAML 测试用例的主函数
    
    Args:
        tests_data_dir: tests_data 目录路径
        
    Returns:
        dict: 扫描结果统计
    """
    from django.conf import settings
    
    if tests_data_dir is None:
        tests_data_dir = settings.WEBAUTO_ROOT / 'tests_data'
    
    scanner = YamlTestScanner(str(tests_data_dir))
    created, updated = scanner.scan_all()
    
    from .models import TestCase
    total = TestCase.objects.filter(file_path__startswith='user/') | \
            TestCase.objects.filter(file_path__startswith='login/') | \
            TestCase.objects.filter(file_path__startswith='e2e/')
    total_count = TestCase.objects.count()
    
    return {
        'created': created,
        'updated': updated,
        'total': total_count,
        'message': f'扫描完成：新增 {created} 条，更新 {updated} 条，共 {total_count} 条用例',
    }
