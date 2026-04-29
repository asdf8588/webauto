# -*- coding: utf-8 -*-
"""
注册登录全链路测试 - 数据驱动 + 动态生成

架构：
  - 测试数据完全来自 YAML 文件
  - YAML 中使用占位符：__AUTO_UUID__, __AUTO_EMAIL__
  - 代码自动将占位符替换为唯一真实值
  - 所有创建的用户自动记录到回滚管理器

使用方式：
  pytest tests/api/test_auth_flow.py -v
  pytest tests/api/test_auth_flow.py -v -k "register"
"""
import pytest
import allure
import os
import yaml

from utils.data_generator import process_auto_fields


# ═══════════════════════════════════════════════════════════════════════════
# 数据加载 - 从 YAML 加载并处理占位符
# ═══════════════════════════════════════════════════════════════════════════
DATA_DIR = os.path.join(os.path.dirname(__file__), "../../data/user")


def _load_yaml(filename):
    """加载 YAML 测试数据"""
    with open(os.path.join(DATA_DIR, filename), "r", encoding="utf-8") as f:
        return yaml.safe_load(f) or []


def _process_case(item):
    """
    处理测试用例：替换占位符为真实值
    
    使用深拷贝确保每次都是唯一数据
    """
    import copy
    case = copy.deepcopy(item)
    return process_auto_fields(case)


def _load_cases(filename):
    """加载并处理用例"""
    cases = []
    for item in _load_yaml(filename):
        # 每个用例使用独立的generated字典，确保${SAME:xxx}在同一用例内保持一致
        processed = process_auto_fields(item)
        cases.append(processed)
    return cases


# 加载所有测试数据
_register_cases = _load_cases("register.yaml")
_login_cases = _load_cases("login.yaml")
_query_cases = _load_cases("query.yaml")
_e2e_cases = _load_cases("e2e.yaml")


# ═══════════════════════════════════════════════════════════════════════════
# 前置步骤执行器
# ═══════════════════════════════════════════════════════════════════════════

def _execute_setup(api_client, rollback_manager, setup_steps):
    """
    执行前置步骤（创建测试用户等）
    
    返回：(user_id, email, password, token)
    """
    result = {"user_id": None, "email": None, "password": None, "token": None}
    
    for step in setup_steps:
        action = step.get("action")
        
        if action == "add_user":
            user_data = {
                "name": step.get("name"),
                "email": step.get("email"),
                "password": step.get("password")
            }
            resp = api_client.add_user(user_data)
            if resp.status_code == 200:
                resp_data = resp.json()
                user_id = resp_data.get("id") or resp_data.get("data", {}).get("id")
                if user_id:
                    rollback_manager.record_user(user_id, step["email"], step["password"])
                    result["user_id"] = user_id
                    result["email"] = step["email"]
                    result["password"] = step["password"]
        
        elif action == "login":
            resp = api_client.login(step.get("email"), step.get("password"))
            if resp.status_code == 200:
                result["token"] = resp.json().get("token")
                api_client.set_token(result["token"])
        
        elif action == "register_login":
            # 注册
            user_data = {
                "name": step.get("name"),
                "email": step.get("email"),
                "password": step.get("password")
            }
            resp = api_client.add_user(user_data)
            if resp.status_code == 200:
                resp_data = resp.json()
                user_id = resp_data.get("id") or resp_data.get("data", {}).get("id")
                if user_id:
                    rollback_manager.record_user(user_id, step["email"], step["password"])
                    result["user_id"] = user_id
                    result["email"] = step["email"]
                    result["password"] = step["password"]
            
            # 登录
            login_resp = api_client.login(step["email"], step["password"])
            if login_resp.status_code == 200:
                result["token"] = login_resp.json().get("token")
                api_client.set_token(result["token"])
        
        elif action == "multi_user_login":
            for u in step.get("users", []):
                user_data = {
                    "name": u.get("name"),
                    "email": u.get("email"),
                    "password": u.get("password")
                }
                resp = api_client.add_user(user_data)
                if resp.status_code == 200:
                    resp_data = resp.json()
                    user_id = resp_data.get("id") or resp_data.get("data", {}).get("id")
                    if user_id:
                        rollback_manager.record_user(user_id, u["email"], u["password"])
                
                login_resp = api_client.login(u["email"], u["password"])
                if login_resp.status_code == 200:
                    result["token"] = login_resp.json().get("token")
                    api_client.set_token(result["token"])
    
    return result


# ═══════════════════════════════════════════════════════════════════════════
# 测试用例 - 完全数据驱动
# ═══════════════════════════════════════════════════════════════════════════

@allure.feature("注册登录全链路")
@allure.story("用户注册")
class TestRegistration:
    """用户注册功能测试"""
    
    @pytest.mark.parametrize("case", _register_cases)
    def test_register(self, api_client, rollback_manager, case):
        """注册测试 - YAML驱动 + 占位符自动替换"""
        allure.dynamic.title(case["name"])
        allure.dynamic.description(case["description"])
        
        # 执行前置 setup
        setup_result = _execute_setup(api_client, rollback_manager, case.get("setup", []))
        
        # 执行注册
        response = api_client.add_user(case["body"])
        
        # 断言
        assert response.status_code == case["expected"]["status"], \
            f"期望 {case['expected']['status']}, 实际 {response.status_code}: {response.text}"
        
        # 如果需要回滚，记录用户
        if response.status_code == 200 and case.get("rollback"):
            resp_data = response.json()
            user_id = resp_data.get("id") or resp_data.get("data", {}).get("id")
            if user_id:
                rollback_manager.record_user(
                    user_id,
                    case["body"].get("email", ""),
                    case["body"].get("password", "")
                )


@allure.feature("注册登录全链路")
@allure.story("用户登录")
class TestLogin:
    """用户登录功能测试"""
    
    @pytest.mark.parametrize("case", _login_cases)
    def test_login(self, api_client, rollback_manager, case):
        """登录测试"""
        allure.dynamic.title(case["name"])
        allure.dynamic.description(case["description"])
        
        # 执行前置 setup
        setup_result = _execute_setup(api_client, rollback_manager, case.get("setup", []))
        
        # 执行登录
        body = case["body"]
        response = api_client.login(body.get("email"), body.get("password"))
        
        # 断言
        assert response.status_code == case["expected"]["status"], \
            f"期望 {case['expected']['status']}, 实际 {response.status_code}: {response.text}"
        
        # 如果需要token，验证返回
        if response.status_code == 200 and case.get("requires_token"):
            resp_data = response.json()
            assert "token" in resp_data, f"期望返回token，实际: {resp_data}"


@allure.feature("注册登录全链路")
@allure.story("认证查询")
class TestAuthentication:
    """认证查询测试"""
    
    @pytest.mark.parametrize("case", _query_cases)
    def test_query(self, api_client, rollback_manager, case):
        """查询测试"""
        allure.dynamic.title(case["name"])
        allure.dynamic.description(case["description"])
        
        # 执行前置 setup
        setup_result = _execute_setup(api_client, rollback_manager, case.get("setup", []))
        
        # 设置认证
        if case.get("requires_auth"):
            if setup_result.get("token"):
                api_client.set_token(setup_result["token"])
            else:
                # 使用默认管理员
                login_resp = api_client.login("admin@example.com", "123456")
                if login_resp.status_code == 200:
                    token = login_resp.json().get("token")
                    if token:
                        api_client.set_token(token)
        
        # 执行查询
        url = case["url"]
        if "{user_id}" in url and setup_result.get("user_id"):
            url = url.replace("{user_id}", str(setup_result["user_id"]))
        
        response = api_client.get(url)
        
        # 断言
        assert response.status_code == case["expected"]["status"], \
            f"期望 {case['expected']['status']}, 实际 {response.status_code}: {response.text}"


@allure.feature("注册登录全链路")
@allure.story("端到端流程")
class TestEndToEnd:
    """端到端流程测试"""
    
    @pytest.mark.parametrize("case", _e2e_cases)
    def test_e2e(self, api_client, rollback_manager, case):
        """端到端测试"""
        allure.dynamic.title(case["name"])
        allure.dynamic.description(case["description"])
        
        # 执行前置 setup
        setup_result = _execute_setup(api_client, rollback_manager, case.get("setup", []))
        
        # 执行主请求
        response = api_client.get(case["url"])
        
        # 断言
        assert response.status_code == case["expected"]["status"], \
            f"期望 {case['expected']['status']}, 实际 {response.status_code}: {response.text}"


# ═══════════════════════════════════════════════════════════════════════════
# 辅助 Fixture
# ═══════════════════════════════════════════════════════════════════════════

@pytest.fixture
def registered_user(api_client, rollback_manager):
    """
    自动注册用户 fixture
    
    用于依赖已注册用户的测试
    """
    from utils.data_generator import gen_uuid
    import time
    
    unique_id = f"{int(time.time() * 1000)}_{gen_uuid()}"
    user_data = {
        "name": f"TestUser_{unique_id}",
        "email": f"test_{unique_id}@example.com",
        "password": "Test@123456"
    }
    
    response = api_client.add_user(user_data)
    if response.status_code != 200:
        pytest.fail(f"注册失败: {response.status_code} - {response.text}")
    
    resp_json = response.json()
    user_id = resp_json.get("id") or resp_json.get("data", {}).get("id")
    
    if not user_id:
        pytest.fail(f"注册成功但未获取到 user_id")
    
    rollback_manager.record_user(user_id, user_data["email"], user_data["password"])
    
    return {
        "user_id": user_id,
        "email": user_data["email"],
        "password": user_data["password"],
        "name": user_data["name"]
    }


@pytest.fixture
def auth_token(api_client, registered_user):
    """登录认证 fixture"""
    response = api_client.login(registered_user["email"], registered_user["password"])
    if response.status_code != 200:
        pytest.fail(f"登录失败: {response.status_code}")
    
    token = response.json().get("token")
    if not token:
        pytest.fail("登录成功但未获取到 token")
    
    api_client.set_token(token)
    return {"token": token, "email": registered_user["email"], "user_id": registered_user["user_id"]}
