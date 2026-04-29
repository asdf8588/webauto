# -*- coding: utf-8 -*-
"""
YAML 用例执行器 - Django 集成版
"""
import os
import yaml
import uuid
import json
from pathlib import Path
from django.conf import settings


class YAMLCaseExecutor:
    """YAML 用例执行器"""
    
    def __init__(self):
        self.base_url = getattr(settings, 'BASE_URL', 'http://localhost:8080')
        # data 目录: d:/pythonshiyan/webauto/data/
        self.data_dir = Path(settings.WEBAUTO_ROOT) / 'data'
        
    def get_yaml_cases(self):
        """获取所有 YAML 用例，按模块分类"""
        cases = []
        categories = {}
        
        if not self.data_dir.exists():
            return {'cases': [], 'categories': {}}
        
        # 扫描 data/ 目录下的所有 .yaml 文件
        for yaml_file in sorted(self.data_dir.glob('*.yaml')):
            module = yaml_file.stem  # 文件名作为模块名
            
            with open(yaml_file, 'r', encoding='utf-8') as f:
                try:
                    data = yaml.safe_load(f)
                    if isinstance(data, list):
                        for case in data:
                            if isinstance(case, dict):
                                case_entry = {
                                    'id': f"{module}/{case.get('case_id', 'unknown')}",
                                    'case_id': case.get('case_id', ''),
                                    'name': case.get('name', ''),
                                    'description': case.get('description', ''),
                                    'method': case.get('method', 'POST'),
                                    'url': case.get('url', ''),
                                    'module': module,
                                    'file': yaml_file.name,
                                    'expected': case.get('expected', {}),
                                    'allure_feature': case.get('allure_feature', module),
                                    'allure_story': case.get('allure_story', ''),
                                    'severity': case.get('severity', 'normal'),
                                }
                                cases.append(case_entry)
                                
                                # 按模块分组
                                if module not in categories:
                                    categories[module] = []
                                categories[module].append(case_entry)
                                
                except Exception as e:
                    print(f"Error loading {yaml_file}: {e}")
        
        return {'cases': cases, 'categories': categories, 'total': len(cases)}
    
    def execute_case(self, case):
        """执行单个用例"""
        import requests
        
        method = case.get('method', 'POST').upper()
        url = case.get('url', '/')
        body = case.get('body', {})
        
        # 替换占位符
        if isinstance(body, dict):
            for k, v in body.items():
                if isinstance(v, str):
                    if '__AUTO_UUID__' in v:
                        body[k] = v.replace('__AUTO_UUID__', uuid.uuid4().hex[:8])
                    if '${SAME:' in v:
                        # 简单处理，实际应该使用上下文中的值
                        body[k] = f"test_{uuid.uuid4().hex[:8]}@example.com"
        
        try:
            full_url = f"{self.base_url}{url}"
            
            if method == 'GET':
                resp = requests.get(full_url, params=body, timeout=30)
            elif method == 'POST':
                resp = requests.post(full_url, json=body, timeout=30)
            elif method == 'PUT':
                resp = requests.put(full_url, json=body, timeout=30)
            elif method == 'PATCH':
                resp = requests.patch(full_url, json=body, timeout=30)
            elif method == 'DELETE':
                resp = requests.delete(full_url, timeout=30)
            else:
                return {'status': 'error', 'error': f'Unsupported method: {method}'}
            
            expected_status = case.get('expected', {}).get('status', 200)
            
            return {
                'status': 'passed' if resp.status_code == expected_status else 'failed',
                'actual_status': resp.status_code,
                'expected_status': expected_status,
                'response': resp.json() if resp.headers.get('content-type', '').startswith('application/json') else resp.text[:200],
            }
        except Exception as e:
            return {'status': 'error', 'error': str(e)}
    
    def run_all(self):
        """执行所有 YAML 用例"""
        result = self.get_yaml_cases()
        cases = result['cases']
        results = []
        
        for case in cases:
            exec_result = self.execute_case(case)
            exec_result['case'] = case
            results.append(exec_result)
            
        return {
            'total': len(results),
            'passed': len([r for r in results if r.get('status') == 'passed']),
            'failed': len([r for r in results if r.get('status') == 'failed']),
            'error': len([r for r in results if r.get('status') == 'error']),
            'results': results
        }
    
    def run_by_module(self, module):
        """按模块执行用例"""
        result = self.get_yaml_cases()
        cases = [c for c in result['cases'] if c['module'] == module]
        
        results = []
        for case in cases:
            exec_result = self.execute_case(case)
            exec_result['case'] = case
            results.append(exec_result)
            
        return {
            'module': module,
            'total': len(results),
            'passed': len([r for r in results if r.get('status') == 'passed']),
            'failed': len([r for r in results if r.get('status') == 'failed']),
            'results': results
        }


def scan_yaml_cases(directory):
    """扫描 YAML 用例（供 Django view 使用）"""
    from apps.cases.models import TestCase
    
    created = updated = 0
    
    data_dir = Path(directory)
    if not data_dir.exists():
        return {'created': 0, 'updated': 0}
    
    for yaml_file in data_dir.glob('*.yaml'):
        module = yaml_file.stem
        file_path = f"yaml:{yaml_file.name}"
        
        try:
            with open(yaml_file, 'r', encoding='utf-8') as f:
                data = yaml.safe_load(f)
                
            if isinstance(data, list):
                for case in data:
                    if isinstance(case, dict) and 'case_id' in case:
                        case_id = f"yaml_{case['case_id']}"
                        name = case.get('name', case.get('case_id', ''))
                        description = case.get('description', '')
                        
                        obj, is_new = TestCase.objects.update_or_create(
                            file_path=file_path,
                            test_id=case_id,
                            defaults={
                                'name': name,
                                'module': module,
                                'case_type': 'api',
                                'description': description,
                                'status': 'active',
                            }
                        )
                        
                        if is_new:
                            created += 1
                        else:
                            updated += 1
                            
        except Exception as e:
            print(f"Error scanning {yaml_file}: {e}")
            
    return {'created': created, 'updated': updated}
