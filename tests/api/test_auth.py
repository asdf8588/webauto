# -*- coding: utf-8 -*-
"""
登录认证API测试
数据驱动模式，从YAML读取测试用例
"""
import pytest
import yaml
import os
import allure

# 加载测试数据
DATA_DIR = os.path.join(os.path.dirname(__file__), "../../data/login")
with open(os.path.join(DATA_DIR, "cases.yaml"), "r", encoding="utf-8") as f:
    test_data_login = yaml.safe_load(f) or []
with open(os.path.join(DATA_DIR, "logout.yaml"), "r", encoding="utf-8") as f:
    test_data_logout = yaml.safe_load(f) or []

# 登录用例
login_cases = [c for c in test_data_login if "login" in c.get("url", "") or c.get("case_id", "").startswith("L")]


@allure.feature("认证模块")
class TestLoginAPI:
    """登录接口测试"""
    
    @pytest.mark.parametrize("case", login_cases)
    def test_login(self, api_client, base_url, case):
        """测试登录接口 - 数据驱动"""
        allure.dynamic.title(case.get("name", "登录测试"))
        allure.dynamic.description(case.get("description", ""))
        allure.dynamic.severity(case.get("severity", "critical"))
        
        with allure.step(f"请求登录 - {case['body'].get('email', '')}"):
            response = api_client.login(case["body"].get("email", ""), case["body"].get("password", ""))
            allure.attach(str(response.json()), "响应", allure.attachment_type.JSON)
        
        with allure.step(f"验证状态码: {case['expected']['status']}"):
            assert response.status_code == case["expected"]["status"], \
                f"期望 {case['expected']['status']}, 实际 {response.status_code}"


@allure.feature("认证模块")
class TestLogoutAPI:
    """登出接口测试"""
    
    @pytest.mark.parametrize("case", test_data_logout)
    def test_logout(self, api_client, base_url, case):
        """测试登出接口 - 数据驱动"""
        allure.dynamic.title(case.get("name", "登出测试"))
        allure.dynamic.description(case.get("description", ""))
        allure.dynamic.severity(case.get("severity", "normal"))
        
        # 前置条件：登录
        if case.get("preconditions"):
            for pre in case["preconditions"]:
                if pre.get("action") == "login":
                    login_resp = api_client.login(pre.get("email", ""), pre.get("password", ""))
                    if login_resp.status_code == 200:
                        token = login_resp.json().get("token")
                        if token:
                            api_client.set_token(token)
        
        with allure.step(f"请求登出"):
            response = api_client.post(case["url"], json=case.get("body", {}))
            allure.attach(f"{response.status_code} {response.text}", "响应", allure.attachment_type.TEXT)
        
        with allure.step(f"验证状态码: {case['expected']['status']}"):
            assert response.status_code == case["expected"]["status"], \
                f"期望 {case['expected']['status']}, 实际 {response.status_code}"
