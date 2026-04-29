# -*- coding: utf-8 -*-
"""
YAML 用例执行器
直接从 data/ 和 test_data/ 目录读取 YAML 用例并执行
"""
import os
import yaml
import uuid
import pytest
import requests
from pathlib import Path
from typing import Dict, List, Any
from datetime import datetime

# 配置
BASE_URL = os.getenv("BASE_URL", "http://localhost:8080")

# 获取 webauto 目录
WEBAUTO_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(WEBAUTO_DIR, "data")
TEST_DATA_DIR = os.path.join(WEBAUTO_DIR, "test_data")


class YAMLCaseExecutor:
    """YAML 用例执行器"""
    
    def __init__(self, base_url: str = None):
        self.base_url = base_url or BASE_URL
        self.session = requests.Session()
        self.session.headers.update({"Content-Type": "application/json"})
        self.results: List[Dict] = []
        
    def replace_placeholders(self, value: Any, context: Dict = None) -> Any:
        """替换占位符"""
        if isinstance(value, str):
            # 替换 __AUTO_UUID__
            if "__AUTO_UUID__" in value:
                value = value.replace("__AUTO_UUID__", uuid.uuid4().hex[:8])
            
            # 替换 ${SAME:key} - 使用上下文中的值
            if context and "${SAME:" in value:
                import re
                matches = re.findall(r'\$\{SAME:(\w+)\}', value)
                for key in matches:
                    if key in context:
                        value = value.replace(f"${{SAME:{key}}}", str(context[key]))
                        
        elif isinstance(value, dict):
            return {k: self.replace_placeholders(v, context) for k, v in value.items()}
        elif isinstance(value, list):
            return [self.replace_placeholders(item, context) for item in value]
            
        return value
    
    def execute_case(self, case: Dict, module: str = "") -> Dict:
        """执行单个用例"""
        case_id = case.get("case_id", "unknown")
        name = case.get("name", "unnamed")
        method = case.get("method", "GET").upper()
        url = case.get("url", "")
        body = case.get("body", {})
        expected = case.get("expected", {})
        
        result = {
            "case_id": case_id,
            "name": name,
            "module": module,
            "method": method,
            "url": url,
            "status": "pending",
            "response": None,
            "error": None,
            "duration": 0
        }
        
        start_time = datetime.now()
        
        try:
            # 处理 setup 动作
            context = {}
            if "setup" in case:
                for action in case["setup"]:
                    if action.get("action") == "add_user":
                        # 先注册用户
                        setup_body = {k: self.replace_placeholders(v) for k, v in action.items() 
                                     if k not in ["action"]}
                        resp = self.session.post(f"{self.base_url}/users/add", json=setup_body)
                        if resp.status_code == 200:
                            data = resp.json()
                            context["dup_email"] = setup_body.get("email")
            
            # 替换占位符
            body = self.replace_placeholders(body, context)
            
            # 发送请求
            full_url = f"{self.base_url}{url}"
            
            if method == "GET":
                resp = self.session.get(full_url, params=body)
            elif method == "POST":
                resp = self.session.post(full_url, json=body)
            elif method == "PUT":
                resp = self.session.put(full_url, json=body)
            elif method == "DELETE":
                resp = self.session.delete(full_url)
            else:
                raise ValueError(f"Unsupported method: {method}")
            
            # 验证结果
            expected_status = expected.get("status", 200)
            expected_type = expected.get("type")
            
            result["response"] = {
                "status_code": resp.status_code,
                "body": resp.json() if resp.headers.get("content-type", "").startswith("application/json") else resp.text
            }
            
            if resp.status_code == expected_status:
                if expected_type:
                    resp_data = result["response"]["body"]
                    if isinstance(resp_data, dict) and resp_data.get("type") == expected_type:
                        result["status"] = "passed"
                    elif expected_type == "error" and resp.status_code >= 400:
                        result["status"] = "passed"
                    else:
                        result["status"] = "failed"
                        result["error"] = f"Expected type '{expected_type}', got '{resp_data.get('type')}'"
                else:
                    result["status"] = "passed"
            else:
                result["status"] = "failed"
                result["error"] = f"Expected status {expected_status}, got {resp.status_code}"
                
        except Exception as e:
            result["status"] = "error"
            result["error"] = str(e)
            
        result["duration"] = (datetime.now() - start_time).total_seconds()
        self.results.append(result)
        
        return result
    
    def execute_from_file(self, file_path: str) -> List[Dict]:
        """从 YAML 文件执行用例"""
        with open(file_path, "r", encoding="utf-8") as f:
            cases = yaml.safe_load(f)
        
        # 获取模块名
        module = Path(file_path).parent.name
        
        results = []
        for case in cases:
            if isinstance(case, dict) and "case_id" in case:
                result = self.execute_case(case, module)
                results.append(result)
                
        return results
    
    def execute_directory(self, directory: str) -> List[Dict]:
        """执行目录下所有 YAML 文件的用例"""
        results = []
        
        for root, dirs, files in os.walk(directory):
            for file in files:
                if file.endswith((".yaml", ".yml")):
                    file_path = os.path.join(root, file)
                    try:
                        file_results = self.execute_from_file(file_path)
                        results.extend(file_results)
                    except Exception as e:
                        print(f"Error executing {file_path}: {e}")
                        
        return results
    
    def print_summary(self):
        """打印执行结果摘要"""
        total = len(self.results)
        passed = sum(1 for r in self.results if r["status"] == "passed")
        failed = sum(1 for r in self.results if r["status"] == "failed")
        errors = sum(1 for r in self.results if r["status"] == "error")
        
        print("\n" + "=" * 60)
        print(f"YAML 用例执行结果摘要")
        print("=" * 60)
        print(f"总计: {total}")
        print(f"通过: {passed} ✅")
        print(f"失败: {failed} ❌")
        print(f"错误: {errors} 💥")
        print("=" * 60)
        
        # 显示失败/错误的详情
        for r in self.results:
            if r["status"] != "passed":
                print(f"\n[{r['status'].upper()}] {r['case_id']} - {r['name']}")
                if r.get("error"):
                    print(f"  错误: {r['error']}")


def pytest_collect_yaml_cases():
    """pytest 钩子：收集所有 YAML 用例"""
    pass


# ============================================================
# Pytest 集成：让 YAML 用例可以被 pytest 执行
# ============================================================

def generate_pytest_from_yaml(yaml_file: str, output_file: str = None) -> str:
    """将 YAML 用例转换为 pytest 测试文件"""
    
    with open(yaml_file, "r", encoding="utf-8") as f:
        cases = yaml.safe_load(f)
    
    module = Path(yaml_file).stem
    cases_dir = Path(yaml_file).parent.name
    
    # 生成 pytest 代码
    lines = [
        '# -*- coding: utf-8 -*-',
        f'"""从 {yaml_file} 生成的 pytest 测试"""\n',
        'import pytest',
        'import requests',
        'import os',
        'from pathlib import Path\n',
        f'BASE_URL = os.getenv("BASE_URL", "http://localhost:8080")\n',
        f'YAML_FILE = r"{yaml_file}"\n',
        'def get_yaml_cases():',
        '    """读取 YAML 用例"""',
        '    import yaml',
        '    with open(YAML_FILE, "r", encoding="utf-8") as f:',
        '        return yaml.safe_load(f)\n',
    ]
    
    lines.append("class TestYAMLGenerated:")
    lines.append(f'    """从 {module}.yaml 生成的测试用例"""\n')
    
    for i, case in enumerate(cases):
        if isinstance(case, dict) and "case_id" in case:
            case_id = case.get("case_id", f"case_{i}")
            name = case.get("name", f"test_case_{i}")
            method = case.get("method", "GET").upper()
            url = case.get("url", "/")
            body = case.get("body", {})
            expected = case.get("expected", {})
            
            # 生成测试函数
            test_name = f"test_{case_id}"
            lines.append(f'    def {test_name}(self):')
            lines.append(f'        """{name}"""')
            lines.append(f'        resp = requests.{method.lower()}(')
            lines.append(f'            f"{{BASE_URL}}{url}",')
            if body:
                lines.append(f'            json={body}')
            lines.append(f'        )')
            
            expected_status = expected.get("status", 200)
            lines.append(f'        assert resp.status_code == {expected_status}')
            lines.append('')
    
    code = "\n".join(lines)
    
    if output_file:
        Path(output_file).write_text(code, encoding="utf-8")
        
    return code


def scan_and_generate_yaml_tests(data_dir: str, output_dir: str) -> int:
    """扫描目录并生成 pytest 测试文件"""
    count = 0
    
    for root, dirs, files in os.walk(data_dir):
        for file in files:
            if file.endswith((".yaml", ".yml")):
                yaml_path = os.path.join(root, file)
                
                # 计算相对路径作为输出目录结构
                rel_path = Path(yaml_path).relative_to(data_dir)
                output_path = Path(output_dir) / "yaml_generated" / rel_path.with_suffix(".py")
                
                output_path.parent.mkdir(parents=True, exist_ok=True)
                
                try:
                    generate_pytest_from_yaml(yaml_path, str(output_path))
                    count += 1
                    print(f"Generated: {output_path}")
                except Exception as e:
                    print(f"Error generating {yaml_path}: {e}")
                    
    return count


# 如果直接运行，执行所有 YAML 用例
if __name__ == "__main__":
    import sys
    
    executor = YAMLCaseExecutor()
    
    # 执行 data/ 目录
    print("\n>>> 执行 data/ 目录的用例...")
    results1 = executor.execute_directory(DATA_DIR)
    
    # 执行 test_data/ 目录
    print("\n>>> 执行 test_data/ 目录的用例...")
    results2 = executor.execute_directory(TEST_DATA_DIR)
    
    # 打印摘要
    executor.print_summary()
    
    # 返回退出码
    failed = sum(1 for r in executor.results if r["status"] != "passed")
    sys.exit(0 if failed == 0 else 1)
