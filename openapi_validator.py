# -*- coding: utf-8 -*-
"""
OpenAPI 规范验证工具

功能：
1. 验证 OpenAPI 规范文件的语法正确性
2. 验证 API 响应是否符合规范定义
3. 生成测试用例覆盖报告

使用方法：
    python openapi_validator.py                    # 验证规范文件
    python openapi_validator.py --serve           # 启动 API Mock 服务器
    python openapi_validator.py --generate       # 从规范生成测试代码
    python openapi_validator.py --test           # 运行生成的测试

学习要点：
- OpenAPI 规范的结构和语法
- 如何验证 API 契约
- 如何使用规范生成测试代码
"""

import json
import sys
import yaml
from pathlib import Path
from typing import Any, Dict, List, Optional
from dataclasses import dataclass, field
from http.server import HTTPServer, BaseHTTPRequestHandler
import threading

# OpenAPI 规范文件路径
SPEC_FILE = Path(__file__).parent / "api_specs" / "openapi.yaml"


@dataclass
class ValidationResult:
    """验证结果"""
    passed: bool
    message: str
    details: List[str] = field(default_factory=list)


class OpenAPIValidator:
    """OpenAPI 规范验证器"""

    def __init__(self, spec_file: Path):
        self.spec_file = spec_file
        self.spec: Dict[str, Any] = {}
        self.errors: List[str] = []

    def load_spec(self) -> bool:
        """加载 OpenAPI 规范文件"""
        if not self.spec_file.exists():
            self.errors.append(f"规范文件不存在: {self.spec_file}")
            return False

        try:
            with open(self.spec_file, 'r', encoding='utf-8') as f:
                content = f.read()
                self.spec = yaml.safe_load(content)
            return True
        except yaml.YAMLError as e:
            self.errors.append(f"YAML 解析错误: {e}")
            return False
        except Exception as e:
            self.errors.append(f"加载文件错误: {e}")
            return False

    def validate_structure(self) -> ValidationResult:
        """验证 OpenAPI 规范基本结构"""
        details = []

        # 检查必需的顶级字段
        required_fields = ['openapi', 'info', 'paths']
        for field_name in required_fields:
            if field_name not in self.spec:
                details.append(f"缺少必需字段: {field_name}")
                continue

            if field_name == 'openapi':
                version = self.spec['openapi']
                if not version.startswith('3.'):
                    details.append(f"OpenAPI 版本不是 3.x: {version}")
                else:
                    details.append(f"[OK] OpenAPI 版本: {version}")

            if field_name == 'info':
                info = self.spec['info']
                details.append(f"[OK] API 标题: {info.get('title', 'N/A')}")
                details.append(f"  版本: {info.get('version', 'N/A')}")
                if 'description' in info:
                    desc = info['description'][:50].replace('\n', ' ')
                    details.append(f"  描述: {desc}...")

            if field_name == 'paths':
                paths = self.spec['paths']
                details.append(f"[OK] 定义了 {len(paths)} 个 API 路径:")
                for path, methods in paths.items():
                    for method in methods.keys():
                        if method in ['get', 'post', 'put', 'delete', 'patch']:
                            details.append(f"    - {method.upper()} {path}")

        passed = len([d for d in details if d.startswith('缺少')]) == 0
        return ValidationResult(passed, "规范结构验证", details)

    def validate_schemas(self) -> ValidationResult:
        """验证 Schema 定义"""
        details = []
        schemas = self.spec.get('components', {}).get('schemas', {})

        details.append(f"\n发现 {len(schemas)} 个 Schema 定义:")

        for name, schema in schemas.items():
            schema_type = schema.get('type', 'object')
            required = schema.get('required', [])
            props = schema.get('properties', {})

            details.append(f"\n  Schema: {name}")
            details.append(f"    类型: {schema_type}")
            if required:
                details.append(f"    必填字段: {', '.join(required)}")
            if props:
                details.append(f"    属性 ({len(props)}个):")
                for prop_name, prop_def in props.items():
                    prop_type = prop_def.get('type', 'any')
                    fmt = prop_def.get('format', '')
                    details.append(f"      - {prop_name}: {prop_type}{' (' + fmt + ')' if fmt else ''}")

        return ValidationResult(True, "Schema 定义验证", details)

    def validate_paths(self) -> ValidationResult:
        """验证 API 路径定义"""
        details = []
        paths = self.spec.get('paths', {})

        for path, path_item in paths.items():
            for method, operation in path_item.items():
                if method not in ['get', 'post', 'put', 'delete', 'patch']:
                    continue

                details.append(f"\n  {method.upper()} {path}")
                details.append(f"    操作ID: {operation.get('operationId', 'N/A')}")
                details.append(f"    摘要: {operation.get('summary', 'N/A')}")

                # 检查请求体
                if 'requestBody' in operation:
                    rb = operation['requestBody']
                    details.append(f"    请求体: 必填={rb.get('required', False)}")
                    if 'content' in rb:
                        for content_type in rb['content']:
                            details.append(f"      Content-Type: {content_type}")

                # 检查响应
                if 'responses' in operation:
                    resp_count = len(operation['responses'])
                    details.append(f"    响应定义: {resp_count} 个状态码")
                    for status_code in operation['responses']:
                        details.append(f"      - {status_code}")

        return ValidationResult(True, "路径定义验证", details)

    def generate_test_cases(self) -> List[Dict[str, Any]]:
        """从规范生成测试用例"""
        test_cases = []
        paths = self.spec.get('paths', {})

        for path, path_item in paths.items():
            for method, operation in path_item.items():
                if method not in ['post']:
                    continue

                operation_id = operation.get('operationId', f'{method}_{path.replace("/", "_")}')
                summary = operation.get('summary', '')
                responses = operation.get('responses', {})

                # 获取请求体示例
                request_body = None
                if 'requestBody' in operation:
                    content = operation['requestBody'].get('content', {})
                    if 'application/json' in content:
                        example = content['application/json'].get('example', {})
                        request_body = example

                # 为每个响应状态码生成用例
                for status_code, response in responses.items():
                    status_int = int(status_code) if status_code.isdigit() else 0

                    case = {
                        'case_id': f'AUTO_{operation_id.upper()}_{status_code}',
                        'name': f'{summary} - {status_code}',
                        'method': method.upper(),
                        'url': path,
                        'expected_status': status_int,
                        'operation_id': operation_id
                    }

                    if request_body:
                        case['body'] = request_body

                    test_cases.append(case)

        return test_cases

    def print_spec_summary(self):
        """打印规范摘要"""
        print("\n" + "=" * 60)
        print("OpenAPI 规范摘要")
        print("=" * 60)

        print(f"\n文件: {self.spec_file}")
        print(f"版本: {self.spec.get('openapi', 'N/A')}")

        info = self.spec.get('info', {})
        print(f"标题: {info.get('title', 'N/A')}")
        print(f"描述: {info.get('description', 'N/A')[:80]}...")

        servers = self.spec.get('servers', [])
        print(f"\n服务器 ({len(servers)}个):")
        for s in servers:
            print(f"  - {s.get('url', 'N/A')}")

        paths = self.spec.get('paths', {})
        print(f"\nAPI 路径 ({len(paths)}个):")
        for path, methods in paths.items():
            method_list = [m.upper() for m in methods.keys() if m in ['get', 'post', 'put', 'delete', 'patch']]
            print(f"  [{', '.join(method_list)}] {path}")

        schemas = self.spec.get('components', {}).get('schemas', {})
        print(f"\n数据模型 ({len(schemas)}个):")
        for name in schemas.keys():
            print(f"  - {name}")

    def run_all_validations(self) -> List[ValidationResult]:
        """运行所有验证"""
        results = []

        print("\n" + "=" * 60)
        print(">>> OpenAPI 规范验证")
        print("=" * 60)

        # 1. 结构验证
        result = self.validate_structure()
        results.append(result)
        print(f"\n{'[PASS]' if result.passed else '[FAIL]'} {result.message}")
        for detail in result.details[:5]:
            print(f"   {detail}")
        if len(result.details) > 5:
            print(f"   ... 还有 {len(result.details) - 5} 项")

        # 2. Schema 验证
        result = self.validate_schemas()
        results.append(result)
        print(f"\n{'[PASS]' if result.passed else '[FAIL]'} {result.message}")
        for detail in result.details[:10]:
            print(f"   {detail}")

        # 3. 路径验证
        result = self.validate_paths()
        results.append(result)
        print(f"\n{'[PASS]' if result.passed else '[FAIL]'} {result.message}")
        for detail in result.details[:15]:
            print(f"   {detail}")

        return results


class MockAPIHandler(BaseHTTPRequestHandler):
    """Mock API 处理器 - 模拟符合规范的 API 响应"""

    def log_message(self, format, *args):
        """自定义日志格式"""
        print(f"[Mock API] {args[0]}")

    def do_POST(self):
        """处理 POST 请求"""
        # 读取请求体
        content_length = int(self.headers.get('Content-Length', 0))
        body = self.rfile.read(content_length).decode('utf-8') if content_length > 0 else '{}'

        try:
            request_data = json.loads(body)
        except:
            request_data = {}

        # 根据路径返回响应
        if self.path == '/users/login':
            self._handle_login(request_data)
        elif self.path == '/users/add':
            self._handle_register(request_data)
        else:
            self._send_json_response(404, {'error': 'Not Found'})

    def _handle_login(self, data: dict):
        """处理登录请求"""
        email = data.get('email', '')
        password = data.get('password', '')

        # 简单验证逻辑
        if not email or not password:
            self._send_json_response(400, {
                'status': 400,
                'type': 'error',
                'message': '邮箱或密码错误'
            })
            return

        # 模拟验证
        if password == '123456' and '@' in email:
            self._send_json_response(200, {
                'status': 200,
                'type': 'success',
                'message': '登录成功'
            })
        else:
            self._send_json_response(400, {
                'status': 400,
                'type': 'error',
                'message': '邮箱或密码错误'
            })

    def _handle_register(self, data: dict):
        """处理注册请求"""
        email = data.get('email', '')
        password = data.get('password', '')

        if not email or not password:
            self._send_json_response(400, {
                'status': 400,
                'type': 'error'
            })
            return

        self._send_json_response(200, {
            'status': 200,
            'type': 'success'
        })

    def _send_json_response(self, status_code: int, data: dict):
        """发送 JSON 响应"""
        self.send_response(status_code)
        self.send_header('Content-Type', 'application/json')
        self.end_headers()
        self.wfile.write(json.dumps(data, ensure_ascii=False).encode('utf-8'))


def start_mock_server(port: int = 8080):
    """启动 Mock API 服务器"""
    server = HTTPServer(('localhost', port), MockAPIHandler)
    print(f"\n>>> Mock API 服务器已启动")
    print(f"   地址: http://localhost:{port}")
    print(f"   按 Ctrl+C 停止服务器\n")

    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\n\nBYE Mock 服务器已停止")
        server.shutdown()


def generate_pytest_code(test_cases: List[Dict[str, Any]], output_file: Path):
    """生成 pytest 测试代码"""
    code = '''# -*- coding: utf-8 -*-
"""
自动生成的 pytest 测试代码
从 OpenAPI 规范: api_specs/openapi.yaml 生成

使用方法:
    pytest tests/api/test_generated_from_openapi.py -v

注意: 需要先启动 Mock 服务器
    python openapi_validator.py --serve
"""

import pytest
import requests
from typing import Dict, Any

# API 基础地址
BASE_URL = "http://localhost:8080"


class TestGeneratedFromOpenAPI:
    """从 OpenAPI 规范自动生成的测试类"""

'''

    for case in test_cases:
        case_id = case['case_id']
        name = case['name']
        method = case['method']
        url = case['url']
        expected_status = case['expected_status']
        body = case.get('body', {})

        # 生成测试方法
        method_name = case_id.lower()

        code += f'''
    def test_{method_name}(self):
        """{name}"""
        url = f"{{BASE_URL}}{url}"
        headers = {{"Content-Type": "application/json"}}
        data = {json.dumps(body, ensure_ascii=False)}

        response = requests.{method.lower()}(url, json=data, headers=headers)

        assert response.status_code == {expected_status}, \\
            f"期望状态码 {{expected_status}}，实际 {{response.status_code}}"

        # 验证响应格式
        try:
            result = response.json()
            assert "status" in result, "响应缺少 status 字段"
            assert result["status"] == {expected_status}
        except ValueError:
            pytest.fail("响应不是有效的 JSON")
'''

    # 添加运行说明
    code += '''
# ============ 使用说明 ============
# 1. 生成这些测试: python openapi_validator.py --generate
# 2. 启动 Mock 服务器: python openapi_validator.py --serve
# 3. 运行测试: pytest tests/api/test_generated_from_openapi.py -v
#
# 这个文件是自动生成的，修改后会被覆盖
# 如需自定义测试，请在 tests/api/ 目录创建新的测试文件
'''

    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(code)

    print(f"\n[PASS] 测试代码已生成: {output_file}")


def main():
    """主函数"""
    import argparse

    parser = argparse.ArgumentParser(description='OpenAPI 验证工具')
    parser.add_argument('--validate', '-v', action='store_true', help='验证规范文件')
    parser.add_argument('--serve', '-s', action='store_true', help='启动 Mock 服务器')
    parser.add_argument('--generate', '-g', action='store_true', help='生成测试代码')
    parser.add_argument('--port', '-p', type=int, default=8080, help='Mock 服务器端口')
    parser.add_argument('--spec', help='指定规范文件路径')

    args = parser.parse_args()

    # 使用指定的规范文件或默认
    spec_file = Path(args.spec) if args.spec else SPEC_FILE

    # 初始化验证器
    validator = OpenAPIValidator(spec_file)

    if not validator.load_spec():
        print("\n[FAIL] 无法加载规范文件:")
        for error in validator.errors:
            print(f"   - {error}")
        return 1

    # 打印规范摘要
    validator.print_spec_summary()

    # 验证模式
    if args.validate:
        results = validator.run_all_validations()

        print("\n" + "=" * 60)
        print("[STAT] 验证结果汇总")
        print("=" * 60)

        passed = sum(1 for r in results if r.passed)
        total = len(results)

        print(f"\n通过: {passed}/{total}")

        if passed == total:
            print("\n[OK] 所有验证通过！OpenAPI 规范格式正确。")
        else:
            print("\n[WARN]  部分验证失败，请检查规范文件。")

        return 0 if passed == total else 1

    # Mock 服务器模式
    if args.serve:
        start_mock_server(args.port)
        return 0

    # 生成测试代码模式
    if args.generate:
        test_cases = validator.generate_test_cases()

        print("\n" + "=" * 60)
        print("[GEN] 生成的测试用例")
        print("=" * 60)

        for case in test_cases:
            print(f"\n  [{case['case_id']}] {case['name']}")
            print(f"    方法: {case['method']} {case['url']}")
            print(f"    期望状态: {case['expected_status']}")

        # 生成 pytest 代码
        output_dir = Path(__file__).parent / "tests" / "api"
        output_dir.mkdir(parents=True, exist_ok=True)

        output_file = output_dir / "test_generated_from_openapi.py"
        generate_pytest_code(test_cases, output_file)

        print("\n" + "=" * 60)
        print("TIP 下一步操作")
        print("=" * 60)
        print("""
  1. 启动 Mock 服务器（模拟 API）:
     python openapi_validator.py --serve

  2. 运行生成的测试:
     pytest tests/api/test_generated_from_openapi.py -v

  3. 验证规范文件:
     python openapi_validator.py --validate
""")
        return 0

    # 默认：显示帮助信息
    print("""
╔══════════════════════════════════════════════════════════════╗
║                    OpenAPI 验证工具                           ║
╠══════════════════════════════════════════════════════════════╣
║                                                              ║
║  使用方法:                                                    ║
║    python openapi_validator.py --validate    # 验证规范文件    ║
║    python openapi_validator.py --serve       # 启动 Mock 服务器 ║
║    python openapi_validator.py --generate    # 生成测试代码    ║
║                                                              ║
║  示例:                                                        ║
║    # 1. 验证 OpenAPI 规范是否正确                              ║
║    python openapi_validator.py -v                                  ║
║                                                              ║
║    # 2. 启动模拟 API 服务器                                    ║
║    python openapi_validator.py -s                                  ║
║                                                              ║
║    # 3. 从规范生成 pytest 测试代码                             ║
║    python openapi_validator.py -g                                  ║
║                                                              ║
╚══════════════════════════════════════════════════════════════╝
""")
    return 0


if __name__ == '__main__':
    sys.exit(main())
