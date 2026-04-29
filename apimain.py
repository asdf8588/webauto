# -*- coding: utf-8 -*-
"""
OpenAPI 一键运行工具

功能：
    验证规范 -> 生成测试 -> 启动 Mock -> 运行测试

使用：
    python apimain.py              # 完整流程
    python apimain.py --validate    # 仅验证规范
    python apimain.py --generate    # 仅生成测试
    python apimain.py --mock        # 仅启动 Mock 服务器
    python apimain.py --test       # 仅运行测试
"""

import sys
import time
import subprocess
import threading
import argparse
from pathlib import Path
from http.server import HTTPServer, BaseHTTPRequestHandler
import json

# 导入验证器
sys.path.insert(0, str(Path(__file__).parent))
from openapi_validator import OpenAPIValidator, SPEC_FILE


class MockHandler(BaseHTTPRequestHandler):
    """Mock API 处理器"""
    
    def log_message(self, format, *args):
        print(f"  [Mock] {args[0]}")
    
    def do_POST(self):
        content_length = int(self.headers.get('Content-Length', 0))
        body = self.rfile.read(content_length).decode('utf-8') if content_length > 0 else '{}'
        
        try:
            data = json.loads(body)
        except:
            data = {}
        
        # 登录接口
        if self.path == '/users/login':
            email = data.get('email', '')
            password = data.get('password', '')
            
            if not email or not password:
                status, response = 400, {'status': 400, 'type': 'error', 'message': '邮箱或密码错误'}
            elif password == '123456' and '@' in email:
                status, response = 200, {'status': 200, 'type': 'success', 'message': '登录成功'}
            else:
                status, response = 400, {'status': 400, 'type': 'error', 'message': '邮箱或密码错误'}
        
        # 注册接口
        elif self.path == '/users/add':
            email = data.get('email', '')
            password = data.get('password', '')
            
            if not email or not password:
                status, response = 400, {'status': 400, 'type': 'error'}
            else:
                status, response = 200, {'status': 200, 'type': 'success'}
        
        else:
            status, response = 404, {'error': 'Not Found'}
        
        self.send_response(status)
        self.send_header('Content-Type', 'application/json')
        self.end_headers()
        self.wfile.write(json.dumps(response, ensure_ascii=False).encode('utf-8'))


def run_mock_server(port: int = 8080):
    """启动 Mock 服务器"""
    server = HTTPServer(('localhost', port), MockHandler)
    print(f"\n启动 Mock 服务器: http://localhost:{port}")
    print("按 Ctrl+C 停止...\n")
    server.serve_forever()


def step1_validate():
    """步骤1：验证规范"""
    print("\n" + "=" * 60)
    print("Step 1: 验证 OpenAPI 规范")
    print("=" * 60)
    
    validator = OpenAPIValidator(SPEC_FILE)
    
    if not validator.load_spec():
        print("\n[FAIL] 无法加载规范文件:")
        for error in validator.errors:
            print(f"   - {error}")
        return False
    
    validator.print_spec_summary()
    results = validator.run_all_validations()
    
    passed = sum(1 for r in results if r.passed)
    print(f"\n通过: {passed}/{len(results)}")
    
    return passed == len(results)


def step2_generate():
    """步骤2：生成测试"""
    print("\n" + "=" * 60)
    print("Step 2: 生成测试代码")
    print("=" * 60)
    
    validator = OpenAPIValidator(SPEC_FILE)
    
    if not validator.load_spec():
        print("[FAIL] 无法加载规范文件")
        return False
    
    test_cases = validator.generate_test_cases()
    
    print(f"\n生成 {len(test_cases)} 个测试用例:\n")
    for case in test_cases:
        print(f"  [{case['case_id']}] {case['name']}")
    
    # 生成测试代码
    code = '''# -*- coding: utf-8 -*-
"""自动生成的测试 - 来自 OpenAPI 规范"""

import pytest
import requests

BASE_URL = "http://localhost:8080"


class TestOpenAPI:
'''

    for case in test_cases:
        method_name = case['case_id'].lower()
        code += f'''
    def test_{method_name}(self):
        """{case['name']}"""
        response = requests.{case['method'].lower()}(
            f"{{BASE_URL}}{case['url']}",
            json={json.dumps(case.get('body', {}))},
            headers={{"Content-Type": "application/json"}}
        )
        assert response.status_code == {case['expected_status']}
'''

    output_file = Path(__file__).parent / "tests" / "api" / "test_openapi_auto.py"
    output_file.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(code)
    
    print(f"\n[PASS] 测试代码已生成: {output_file}")
    return True


def step3_run_tests():
    """步骤3：运行测试"""
    print("\n" + "=" * 60)
    print("Step 3: 运行测试")
    print("=" * 60)
    
    test_file = Path(__file__).parent / "tests" / "api" / "test_openapi_auto.py"
    
    if not test_file.exists():
        print(f"[FAIL] 测试文件不存在: {test_file}")
        return False
    
    print(f"\n运行测试文件: {test_file.name}\n")
    
    result = subprocess.run(
        ["pytest", str(test_file), "-v", "--tb=short"],
        capture_output=False
    )
    
    return result.returncode == 0


def main():
    parser = argparse.ArgumentParser(description='OpenAPI 一键运行工具')
    parser.add_argument('--validate', '-v', action='store_true', help='仅验证规范')
    parser.add_argument('--generate', '-g', action='store_true', help='仅生成测试')
    parser.add_argument('--mock', '-m', action='store_true', help='仅启动 Mock')
    parser.add_argument('--test', '-t', action='store_true', help='仅运行测试')
    parser.add_argument('--port', '-p', type=int, default=8080, help='Mock 端口')
    
    args = parser.parse_args()
    
    # 判断模式
    has_specific = args.validate or args.generate or args.mock or args.test
    run_all = not has_specific
    
    print("""
+============================================================+
|                    OpenAPI 一键运行                        |
|                                                            |
|  功能：验证规范 -> 生成测试 -> 启动Mock -> 运行测试          |
+============================================================+
""")
    
    # 仅 Mock 模式
    if args.mock:
        run_mock_server(args.port)
        return 0
    
    # 步骤1：验证
    if run_all or args.validate:
        if not step1_validate():
            return 1
        if args.validate:
            return 0
    
    # 步骤2：生成
    if run_all or args.generate:
        if not step2_generate():
            return 1
        if args.generate:
            return 0
    
    # 步骤3：Mock + 测试
    if run_all or args.test:
        print("\n" + "=" * 60)
        print("Step 3: 启动 Mock 服务器并运行测试")
        print("=" * 60)
        
        # 启动 Mock 服务器（后台线程）
        print(f"\n启动 Mock 服务器: http://localhost:{args.port}")
        mock_thread = threading.Thread(target=run_mock_server, args=(args.port,), daemon=True)
        mock_thread.start()
        
        # 等待服务器启动
        time.sleep(1)
        
        # 运行测试
        success = step3_run_tests()
        
        print("\n" + "=" * 60)
        if success:
            print(">>> 测试全部通过!")
        else:
            print(">>> 部分测试失败")
        print("=" * 60)
        
        return 0 if success else 1
    
    return 0


if __name__ == '__main__':
    sys.exit(main())
