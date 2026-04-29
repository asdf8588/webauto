# -*- coding: utf-8 -*-
"""
OpenAPI 和 Trace 相关 API Views
"""
import os
import json
import yaml
import uuid
from datetime import datetime
from django.conf import settings
from rest_framework.views import APIView
from rest_framework.response import Response


class YAMLCasesAPIView(APIView):
    """YAML 用例管理 API"""
    
    def get(self, request):
        """获取所有 YAML 用例"""
        cases = []
        
        # 读取 data/ 目录
        data_dir = getattr(settings, 'WEBAUTO_DATA_DIR', None)
        if data_dir and os.path.exists(data_dir):
            for root, dirs, files in os.walk(data_dir):
                for file in files:
                    if file.endswith('.yaml') or file.endswith('.yml'):
                        filepath = os.path.join(root, files)
                        module = os.path.basename(root)
                        with open(filepath, 'r', encoding='utf-8') as f:
                            try:
                                data = yaml.safe_load(f)
                                if isinstance(data, list):
                                    for item in data:
                                        item['module'] = module
                                        item['source'] = 'data'
                                        cases.append(item)
                                elif isinstance(data, dict):
                                    data['module'] = module
                                    data['source'] = 'data'
                                    cases.append(data)
                            except:
                                pass
        
        # 读取 test_data/ 目录
        test_data_dir = getattr(settings, 'WEBAUTO_TEST_DATA_DIR', None)
        if test_data_dir and os.path.exists(test_data_dir):
            for root, dirs, files in os.walk(test_data_dir):
                for file in files:
                    if file.endswith('.yaml') or file.endswith('.yml'):
                        filepath = os.path.join(root, file)
                        module = os.path.basename(root)
                        with open(filepath, 'r', encoding='utf-8') as f:
                            try:
                                data = yaml.safe_load(f)
                                if isinstance(data, list):
                                    for item in data:
                                        item['module'] = module
                                        item['source'] = 'test_data'
                                        cases.append(item)
                                elif isinstance(data, dict):
                                    data['module'] = module
                                    data['source'] = 'test_data'
                                    cases.append(data)
                            except:
                                pass
        
        return Response(cases)


class RunYAMLAPIView(APIView):
    """执行 YAML 用例"""
    
    def post(self, request, case_id=None):
        """执行 YAML 测试用例"""
        from webauto.yaml_runner import YAMLCaseExecutor
        
        executor = YAMLCaseExecutor()
        
        if case_id:
            # 执行单个用例
            result = executor.run_case_by_id(case_id)
            return Response({'case_id': case_id, 'result': result})
        else:
            # 执行所有用例
            results = executor.run_all()
            return Response({
                'total': len(results),
                'passed': sum(1 for r in results if r.get('result', {}).get('status') == 'passed'),
                'failed': sum(1 for r in results if r.get('result', {}).get('status') == 'failed'),
                'results': results
            })


class GenerateFromOpenAPIView(APIView):
    """从 OpenAPI 规范生成测试用例"""
    
    def post(self, request):
        """根据 OpenAPI 规范生成测试用例"""
        spec = request.data.get('spec', {})
        base_url = request.data.get('base_url', os.getenv('BASE_URL', 'http://localhost:8080'))
        
        cases = []
        
        for path, methods in spec.get('paths', {}).items():
            for method, details in methods.items():
                if method.upper() in ('GET', 'POST', 'PUT', 'DELETE', 'PATCH'):
                    case = {
                        'case_id': f'openapi_{method.upper()}_{path.replace("/", "_").strip("_")}',
                        'name': details.get('summary', details.get('operationId', f'{method.upper()} {path}')),
                        'method': method.upper(),
                        'url': path,
                        'module': 'openapi',
                        'description': details.get('description', ''),
                        'body': {},
                        'expected': {
                            'status': 200
                        },
                        'tags': ['openapi', 'auto-generated']
                    }
                    
                    # 处理请求体
                    request_body = details.get('requestBody', {})
                    if request_body:
                        content = request_body.get('content', {})
                        json_content = content.get('application/json', {})
                        schema = json_content.get('schema', {})
                        
                        # 生成示例请求体
                        case['body'] = self._generate_example(schema)
                    
                    cases.append(case)
        
        return Response({
            'count': len(cases),
            'cases': cases
        })
    
    def _generate_example(self, schema):
        """根据 schema 生成示例数据"""
        example = {}
        
        if not schema:
            return example
        
        properties = schema.get('properties', {})
        
        for key, prop in properties.items():
            prop_type = prop.get('type', 'string')
            enum = prop.get('enum', [])
            
            if enum:
                example[key] = enum[0]
            elif prop_type == 'string':
                if 'email' in key.lower():
                    example[key] = 'test@example.com'
                elif 'name' in key.lower():
                    example[key] = 'Test User'
                elif 'password' in key.lower():
                    example[key] = 'Password123'
                elif 'phone' in key.lower():
                    example[key] = '13800138000'
                elif 'id' in key.lower():
                    example[key] = str(uuid.uuid4())[:8]
                else:
                    example[key] = 'string'
            elif prop_type == 'integer':
                example[key] = 0
            elif prop_type == 'number':
                example[key] = 0.0
            elif prop_type == 'boolean':
                example[key] = True
            elif prop_type == 'array':
                example[key] = []
            elif prop_type == 'object':
                example[key] = self._generate_example(prop)
        
        return example


class SaveOpenAPIToYAMLView(APIView):
    """保存 OpenAPI 生成的用例到 YAML 文件"""
    
    def post(self, request):
        """保存 OpenAPI 用例到 data/openapi/ 目录"""
        spec = request.data.get('spec', {})
        
        # 创建 openapi 目录
        data_dir = getattr(settings, 'WEBAUTO_DATA_DIR', None)
        if not data_dir:
            data_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))), 'data')
        
        openapi_dir = os.path.join(data_dir, 'openapi')
        os.makedirs(openapi_dir, exist_ok=True)
        
        # 按模块分组
        modules = {}
        
        for path, methods in spec.get('paths', {}).items():
            for method, details in methods.items():
                if method.upper() in ('GET', 'POST', 'PUT', 'DELETE', 'PATCH'):
                    module = details.get('tags', ['default'])[0].lower().replace(' ', '_')
                    
                    if module not in modules:
                        modules[module] = []
                    
                    case = {
                        'case_id': f'openapi_{method.upper()}_{path.replace("/", "_").strip("_")}',
                        'name': details.get('summary', details.get('operationId', f'{method.upper()} {path}')),
                        'method': method.upper(),
                        'url': path,
                        'description': details.get('description', ''),
                        'tags': ['openapi', 'auto-generated']
                    }
                    
                    # 处理请求体
                    request_body = details.get('requestBody', {})
                    if request_body:
                        content = request_body.get('content', {})
                        json_content = content.get('application/json', {})
                        schema = json_content.get('schema', {})
                        case['body'] = self._generate_example(schema)
                    
                    modules[module].append(case)
        
        # 写入文件
        count = 0
        for module, cases in modules.items():
            filepath = os.path.join(openapi_dir, f'{module}.yaml')
            with open(filepath, 'w', encoding='utf-8') as f:
                yaml.dump(cases, f, allow_unicode=True, default_flow_style=False)
            count += len(cases)
        
        return Response({
            'message': f'已保存 {count} 个用例到 {openapi_dir}',
            'count': count,
            'files': list(modules.keys())
        })
    
    def _generate_example(self, schema):
        """根据 schema 生成示例数据"""
        example = {}
        
        if not schema:
            return example
        
        properties = schema.get('properties', {})
        
        for key, prop in properties.items():
            prop_type = prop.get('type', 'string')
            enum = prop.get('enum', [])
            
            if enum:
                example[key] = enum[0]
            elif prop_type == 'string':
                if 'email' in key.lower():
                    example[key] = 'test@example.com'
                elif 'name' in key.lower():
                    example[key] = 'Test User'
                elif 'password' in key.lower():
                    example[key] = 'Password123'
                elif 'phone' in key.lower():
                    example[key] = '13800138000'
                elif 'id' in key.lower():
                    example[key] = str(uuid.uuid4())[:8]
                else:
                    example[key] = 'string'
            elif prop_type == 'integer':
                example[key] = 0
            elif prop_type == 'number':
                example[key] = 0.0
            elif prop_type == 'boolean':
                example[key] = True
            elif prop_type == 'array':
                example[key] = []
            elif prop_type == 'object':
                example[key] = self._generate_example(prop)
        
        return example


class TracesAPIView(APIView):
    """Playwright Trace 文件管理"""
    
    def get(self, request):
        """获取所有 Trace 文件列表"""
        traces = []
        
        # 查找 traces 目录
        base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))))
        trace_dirs = [
            os.path.join(base_dir, 'traces'),
            os.path.join(base_dir, 'playwright-traces'),
            os.path.join(base_dir, 'test-results'),
        ]
        
        for trace_dir in trace_dirs:
            if os.path.exists(trace_dir):
                for item in os.listdir(trace_dir):
                    item_path = os.path.join(trace_dir, item)
                    if os.path.isdir(item_path):
                        stat = os.stat(item_path)
                        traces.append({
                            'name': item,
                            'path': item_path,
                            'date': datetime.fromtimestamp(stat.st_mtime).strftime('%Y-%m-%d %H:%M:%S'),
                            'size': self._format_size(stat.st_size)
                        })
        
        return Response(traces)
    
    def _format_size(self, size):
        """格式化文件大小"""
        for unit in ['B', 'KB', 'MB', 'GB']:
            if size < 1024:
                return f"{size:.1f} {unit}"
            size /= 1024
        return f"{size:.1f} TB"


class GenerateReportAPIView(APIView):
    """生成 Allure 报告"""
    
    def post(self, request):
        """生成 Allure HTML 报告"""
        import subprocess
        
        base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))))
        results_dir = os.path.join(base_dir, 'allure-results')
        report_dir = os.path.join(base_dir, 'allure-report')
        
        # 检查结果目录
        if not os.path.exists(results_dir):
            return Response({
                'success': False,
                'error': f'Allure results directory not found: {results_dir}'
            }, status=404)
        
        # 检查是否有结果文件
        if not any(f.endswith('.json') for f in os.listdir(results_dir)):
            return Response({
                'success': False,
                'error': 'No test results found. Run tests first with --alluredir=allure-results'
            }, status=400)
        
        try:
            # 生成报告
            result = subprocess.run(
                ['allure', 'generate', results_dir, '--clean', '-o', report_dir],
                capture_output=True,
                text=True,
                timeout=60
            )
            
            if result.returncode == 0:
                return Response({
                    'success': True,
                    'path': report_dir,
                    'message': 'Report generated successfully!'
                })
            else:
                return Response({
                    'success': False,
                    'error': result.stderr or 'Failed to generate report'
                }, status=500)
                
        except FileNotFoundError:
            return Response({
                'success': False,
                'error': 'Allure CLI not found. Please install: npm install -g allure-commandline'
            }, status=500)
        except subprocess.TimeoutExpired:
            return Response({
                'success': False,
                'error': 'Report generation timed out'
            }, status=500)
        except Exception as e:
            return Response({
                'success': False,
                'error': str(e)
            }, status=500)
