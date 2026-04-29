# -*- coding: utf-8 -*-
"""
统一测试平台 - platform_test.py

整合所有测试用例，统一入口。
支持按模块、按标签、按优先级筛选。

使用方法:
    pytest platform_test.py -v                      # 运行所有测试
    pytest platform_test.py -v -m login            # 只运行登录模块
    pytest platform_test.py -v -m smoke             # 只运行冒烟测试
    pytest platform_test.py -v -m "smoke and P0"   # 冒烟测试 + P0优先级
"""
import pytest
import allure
import sys
import os
import uuid

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from utils.test_case_loader import get_loader, CaseLoader


# ═══════════════════════════════════════════════════════════════════════════
# 加载测试数据
# ═══════════════════════════════════════════════════════════════════════════
loader = get_loader()
ALL_CASES = loader.load_all()


# ═══════════════════════════════════════════════════════════════════════════
# 辅助函数
# ═══════════════════════════════════════════════════════════════════════════
def _execute_setup(api_client, rollback_manager, setup_steps):
    """执行前置步骤"""
    result = {"user_id": None, "email": None, "password": None, "token": None}

    if not setup_steps:
        return result

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
                user_id = resp.json().get("id") or resp.json().get("data", {}).get("id")
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
                user_id = resp.json().get("id") or resp.json().get("data", {}).get("id")
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
                    user_id = resp.json().get("id") or resp.json().get("data", {}).get("id")
                    if user_id:
                        rollback_manager.record_user(user_id, u["email"], u["password"])

                login_resp = api_client.login(u["email"], u["password"])
                if login_resp.status_code == 200:
                    result["token"] = login_resp.json().get("token")
                    api_client.set_token(result["token"])

    return result


# ═══════════════════════════════════════════════════════════════════════════
# 登录测试
# ═══════════════════════════════════════════════════════════════════════════
@allure.feature("登录模块")
class TestLogin:
    """登录功能测试"""

    @pytest.mark.parametrize("case", ALL_CASES.get("login", []))
    def test_login(self, api_client, base_url, case):
        """登录测试"""
        # 解析占位符
        case = CaseLoader.resolve_case(case)

        allure.dynamic.title(case.get("name", "登录测试"))
        allure.dynamic.description(case.get("description", ""))
        allure.dynamic.severity(case.get("priority", "P2"))

        with allure.step(f"请求登录: {case['body'].get('email', '')}"):
            response = api_client.login(
                case["body"].get("email", ""),
                case["body"].get("password", "")
            )
            allure.attach(str(response.json()), "响应", allure.attachment_type.JSON)

        with allure.step(f"验证状态码: {case['expected']['status']}"):
            assert response.status_code == case["expected"]["status"], \
                f"期望 {case['expected']['status']}, 实际 {response.status_code}: {response.text}"


# ═══════════════════════════════════════════════════════════════════════════
# 登出测试
# ═══════════════════════════════════════════════════════════════════════════
@allure.feature("登出模块")
class TestLogout:
    """登出功能测试"""

    @pytest.mark.parametrize("case", ALL_CASES.get("logout", []))
    def test_logout(self, api_client, base_url, case):
        """登出测试"""
        case = CaseLoader.resolve_case(case)

        allure.dynamic.title(case.get("name", "登出测试"))
        allure.dynamic.description(case.get("description", ""))

        # 执行前置条件
        if case.get("preconditions"):
            for pre in case["preconditions"]:
                if pre.get("action") == "login":
                    login_resp = api_client.login(pre.get("email", ""), pre.get("password", ""))
                    if login_resp.status_code == 200:
                        token = login_resp.json().get("token")
                        if token:
                            api_client.set_token(token)

        with allure.step("请求登出"):
            response = api_client.post(case["url"], json=case.get("body", {}))

        with allure.step(f"验证状态码: {case['expected']['status']}"):
            assert response.status_code == case["expected"]["status"], \
                f"期望 {case['expected']['status']}, 实际 {response.status_code}"


# ═══════════════════════════════════════════════════════════════════════════
# 注册测试
# ═══════════════════════════════════════════════════════════════════════════
@allure.feature("注册模块")
class TestRegister:
    """注册功能测试"""

    @pytest.mark.parametrize("case", ALL_CASES.get("register", []))
    def test_register(self, api_client, rollback_manager, case):
        """注册测试"""
        case = CaseLoader.resolve_case(case)

        allure.dynamic.title(case.get("name", "注册测试"))
        allure.dynamic.description(case.get("description", ""))
        allure.dynamic.severity(case.get("priority", "P2"))

        # 执行前置条件
        _execute_setup(api_client, rollback_manager, case.get("setup", []))

        with allure.step(f"发送注册请求"):
            response = api_client.add_user(case["body"])
            allure.attach(str(response.json()), "响应", allure.attachment_type.JSON)

        with allure.step(f"验证状态码: {case['expected']['status']}"):
            assert response.status_code == case["expected"]["status"], \
                f"期望 {case['expected']['status']}, 实际 {response.status_code}: {response.text}"

        # 记录用于回滚
        if response.status_code == 200 and case.get("rollback"):
            user_id = response.json().get("id") or response.json().get("data", {}).get("id")
            if user_id:
                rollback_manager.record_user(
                    user_id,
                    case["body"].get("email", ""),
                    case["body"].get("password", "")
                )


# ═══════════════════════════════════════════════════════════════════════════
# 查询测试
# ═══════════════════════════════════════════════════════════════════════════
@allure.feature("查询模块")
class TestQuery:
    """查询功能测试"""

    @pytest.mark.parametrize("case", ALL_CASES.get("query", []))
    def test_query(self, api_client, rollback_manager, case):
        """查询测试"""
        case = CaseLoader.resolve_case(case)

        allure.dynamic.title(case.get("name", "查询测试"))
        allure.dynamic.description(case.get("description", ""))

        # 执行前置条件
        setup_result = _execute_setup(api_client, rollback_manager, case.get("setup", []))

        # 设置认证
        if case.get("requires_auth") and setup_result.get("token"):
            api_client.set_token(setup_result["token"])

        # 替换URL中的user_id
        url = case["url"]
        if "{user_id}" in url and setup_result.get("user_id"):
            url = url.replace("{user_id}", str(setup_result["user_id"]))

        with allure.step(f"发送查询请求: {url}"):
            response = api_client.get(url)

        with allure.step(f"验证状态码: {case['expected']['status']}"):
            assert response.status_code == case["expected"]["status"], \
                f"期望 {case['expected']['status']}, 实际 {response.status_code}"


# ═══════════════════════════════════════════════════════════════════════════
# 更新测试
# ═══════════════════════════════════════════════════════════════════════════
@allure.feature("更新模块")
class TestUpdate:
    """更新功能测试"""

    @pytest.mark.parametrize("case", ALL_CASES.get("update", []))
    def test_update(self, api_client, rollback_manager, case):
        """更新测试"""
        case = CaseLoader.resolve_case(case)

        allure.dynamic.title(case.get("name", "更新测试"))
        allure.dynamic.description(case.get("description", ""))

        # 创建测试用户
        user_id = None
        temp_email = f"update_test_{uuid.uuid4().hex[:8]}@example.com"
        create_resp = api_client.add_user({
            "name": f"UpdateTest_{uuid.uuid4().hex[:6]}",
            "email": temp_email,
            "password": "Test@123456"
        })
        if create_resp.status_code == 200:
            user_id = create_resp.json().get("id") or create_resp.json().get("data", {}).get("id")
            if user_id:
                rollback_manager.record_user(user_id, temp_email, "Test@123456")

        # 替换URL中的user_id
        url = case["url"]
        if user_id and "{user_id}" in url:
            url = url.replace("{user_id}", str(user_id))

        # 如果URL仍包含{user_id}且没有user_id，跳过
        if "{user_id}" in url:
            pytest.skip("无法获取有效用户ID")

        with allure.step(f"发送更新请求: {url}"):
            method = case.get("method", "PATCH").upper()
            if method == "PUT":
                response = api_client.put(url, json=case.get("body", {}))
            else:
                response = api_client.patch(url, json=case.get("body", {}))

        with allure.step(f"验证状态码: {case['expected']['status']}"):
            assert response.status_code == case["expected"]["status"], \
                f"期望 {case['expected']['status']}, 实际 {response.status_code}"


# ═══════════════════════════════════════════════════════════════════════════
# 删除测试
# ═══════════════════════════════════════════════════════════════════════════
@allure.feature("删除模块")
class TestDelete:
    """删除功能测试"""

    @pytest.mark.parametrize("case", ALL_CASES.get("delete", []))
    def test_delete(self, api_client, rollback_manager, case):
        """删除测试"""
        case = CaseLoader.resolve_case(case)

        allure.dynamic.title(case.get("name", "删除测试"))
        allure.dynamic.description(case.get("description", ""))

        # 创建测试用户
        user_id = None
        temp_email = f"delete_test_{uuid.uuid4().hex[:8]}@example.com"
        create_resp = api_client.add_user({
            "name": f"DeleteTest_{uuid.uuid4().hex[:6]}",
            "email": temp_email,
            "password": "Test@123456"
        })
        if create_resp.status_code == 200:
            user_id = create_resp.json().get("id") or create_resp.json().get("data", {}).get("id")
            if user_id:
                rollback_manager.record_user(user_id, temp_email, "Test@123456")

        # 处理 create_and_delete 场景
        if case.get("setup") == "create_and_delete" and user_id:
            api_client.delete_user(str(user_id))

        # 替换URL中的user_id
        url = case["url"]
        if user_id and "{user_id}" in url:
            url = url.replace("{user_id}", str(user_id))

        with allure.step(f"发送删除请求: {url}"):
            response = api_client.delete_user(url.replace("/users/", ""))

        with allure.step(f"验证状态码: {case['expected']['status']}"):
            assert response.status_code == case["expected"]["status"], \
                f"期望 {case['expected']['status']}, 实际 {response.status_code}"


# ═══════════════════════════════════════════════════════════════════════════
# 端到端测试
# ═══════════════════════════════════════════════════════════════════════════
@allure.feature("端到端模块")
class TestE2E:
    """端到端测试"""

    @pytest.mark.parametrize("case", ALL_CASES.get("e2e", []))
    def test_e2e(self, api_client, rollback_manager, case):
        """端到端测试"""
        case = CaseLoader.resolve_case(case)

        allure.dynamic.title(case.get("name", "E2E测试"))
        allure.dynamic.description(case.get("description", ""))

        # 执行前置条件
        _execute_setup(api_client, rollback_manager, case.get("setup", []))

        with allure.step(f"发送请求: {case.get('method', 'GET')} {case['url']}"):
            method = case.get("method", "GET").upper()
            if method == "GET":
                response = api_client.get(case["url"])
            elif method == "POST":
                response = api_client.post(case["url"], json=case.get("body", {}))

        with allure.step(f"验证状态码: {case['expected']['status']}"):
            assert response.status_code == case["expected"]["status"], \
                f"期望 {case['expected']['status']}, 实际 {response.status_code}"


# ═══════════════════════════════════════════════════════════════════════════
# pytest.ini markers 定义
# ═══════════════════════════════════════════════════════════════════════════
def pytest_configure(config):
    """注册自定义 markers"""
    config.addinivalue_line("markers", "login: 登录模块测试")
    config.addinivalue_line("markers", "logout: 登出模块测试")
    config.addinivalue_line("markers", "register: 注册模块测试")
    config.addinivalue_line("markers", "query: 查询模块测试")
    config.addinivalue_line("markers", "update: 更新模块测试")
    config.addinivalue_line("markers", "delete: 删除模块测试")
    config.addinivalue_line("markers", "e2e: 端到端测试")
    config.addinivalue_line("markers", "smoke: 冒烟测试")
    config.addinivalue_line("markers", "regression: 回归测试")
