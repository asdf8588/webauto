# -*- coding: utf-8 -*-
"""
端到端API测试
数据驱动模式，从YAML读取测试用例
"""
import pytest
import os
import allure
import uuid
import yaml

# 加载测试数据
DATA_DIR = os.path.join(os.path.dirname(__file__), "../../data")
with open(os.path.join(DATA_DIR, "e2e.yaml"), "r", encoding="utf-8") as f:
    test_data_e2e = yaml.safe_load(f) or []


def _process_case(item):
    """处理测试用例数据"""
    unique_id = uuid.uuid4().hex[:8]
    
    # 处理 body 字段
    body = {}
    if "body" in item:
        for k, v in item["body"].items():
            if isinstance(v, str):
                body[k] = v.replace("{unique_id}", unique_id)
            else:
                body[k] = v
    
    # 处理 steps 中的 {unique_id}
    steps = []
    if "steps" in item:
        for step in item["steps"]:
            new_step = dict(step)
            if "data" in step:
                for k, v in step["data"].items():
                    if isinstance(v, str):
                        new_step["data"][k] = v.replace("{unique_id}", unique_id)
            if "email" in step:
                if isinstance(step["email"], str):
                    new_step["email"] = step["email"].replace("{unique_id}", unique_id)
            steps.append(new_step)
    
    return {
        "name": item.get("name", ""),
        "case_id": item.get("case_id", ""),
        "description": item.get("description", ""),
        "body": body,
        "steps": steps,
        "expected_code": item.get("expected", {}).get("status", 200),
        "severity": item.get("severity", "normal"),
    }


e2e_cases = [_process_case(item) for item in test_data_e2e]


@allure.feature("端到端测试")
class TestUserLifecycle:
    """用户生命周期端到端测试"""
    
    @pytest.mark.parametrize("case", e2e_cases)
    def test_e2e(self, api_client, base_url, rollback_manager, case):
        """端到端测试 - 数据驱动"""
        allure.dynamic.title(case["name"])
        allure.dynamic.description(case["description"])
        allure.dynamic.severity(case["severity"])
        
        # 执行步骤
        for step in case["steps"]:
            step_name = step.get("name", "未知步骤")
            action = step.get("action")
            
            with allure.step(f"步骤: {step_name}"):
                if action == "add_user":
                    data = dict(step.get("data", {}))
                    response = api_client.add_user(data)
                    assert response.status_code in [200, 400], f"添加用户失败: {response.status_code}"
                    
                    # 记录创建的用户用于清理
                    if response.status_code == 200:
                        resp_data = response.json()
                        user_id = resp_data.get("id") or resp_data.get("data", {}).get("id")
                        if user_id:
                            rollback_manager.record_user(
                                user_id, 
                                data.get("email", ""), 
                                data.get("password", "")
                            )
                
                elif action == "login":
                    email = step.get("email", "")
                    password = step.get("password", "")
                    response = api_client.login(email, password)
                    assert response.status_code == 200, f"登录失败: {response.status_code}"
                    token = response.json().get("token")
                    if token:
                        api_client.set_token(token)
                
                elif action == "get_users":
                    response = api_client.get_users()
                    expected_status = step.get("expected_status", 200)
                    assert response.status_code == expected_status, f"获取用户列表失败: {response.status_code}"
