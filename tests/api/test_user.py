# -*- coding: utf-8 -*-
"""
用户管理API测试
数据驱动模式，从YAML读取测试用例
"""
import pytest
import yaml
import os
import allure
import uuid
import time
from itertools import cycle

# 查询用户轮询索引（用于均匀分配预创建用户）
_query_user_index = 0

# 加载测试数据
DATA_DIR = os.path.join(os.path.dirname(__file__), "../../data/user")
with open(os.path.join(DATA_DIR, "register.yaml"), "r", encoding="utf-8") as f:
    test_data_register = yaml.safe_load(f) or []
with open(os.path.join(DATA_DIR, "delete.yaml"), "r", encoding="utf-8") as f:
    test_data_delete = yaml.safe_load(f) or []
with open(os.path.join(DATA_DIR, "update.yaml"), "r", encoding="utf-8") as f:
    test_data_update = yaml.safe_load(f) or []
with open(os.path.join(DATA_DIR, "query.yaml"), "r", encoding="utf-8") as f:
    test_data_query = yaml.safe_load(f) or []


def _process_case(item):
    """处理测试用例数据"""
    timestamp = str(int(time.time()))
    unique_id = uuid.uuid4().hex[:6]

    # 处理 body 字段
    body = {}
    if "body" in item:
        for k, v in item["body"].items():
            if isinstance(v, str):
                body[k] = v.replace("{timestamp}", timestamp).replace("{unique_id}", unique_id)
            else:
                body[k] = v

    # 处理 URL 中的 {user_id} 占位符
    user_id = item.get("user_id")
    url = item.get("url", "")
    
    if not user_id:
        if "/users/seek/" in url:
            parts = url.split("/users/seek/")
            if len(parts) > 1:
                user_id = parts[1]
        elif "/users/check/" in url:
            parts = url.split("/users/check/")
            if len(parts) > 1:
                user_id = parts[1]
        elif "/users/" in url and not url.endswith("/users"):
            parts = url.split("/users/")
            if len(parts) > 1:
                user_id = parts[1]

    return {
        "name": item.get("name", ""),
        "case_id": item.get("case_id", ""),
        "data": body,
        "user_id": user_id,
        "expected_code": item.get("expected", {}).get("status", 200),
        "setup": item.get("setup"),
        "severity": item.get("severity", "normal"),
    }


# 转换数据
add_user_cases = [_process_case(item) for item in test_data_register]
update_user_cases = [_process_case(item) for item in test_data_update]
delete_user_cases = [_process_case(item) for item in test_data_delete]
get_user_cases = [_process_case(item) for item in test_data_query]


@allure.feature("用户管理模块")
class TestUserAPI:
    """用户管理接口测试"""
    
    @pytest.fixture(autouse=True)
    def setup(self, api_client, base_url, rollback_manager):
        """每个测试前先登录获取token"""
        self.client = api_client
        self.base_url = base_url
        self.rollback_manager = rollback_manager  # 用于清理测试数据
        
        # 登录获取token
        response = self.client.login("admin@example.com", "123456")
        if response.status_code == 200:
            token = response.json().get("token")
            if token:
                self.client.set_token(token)
    
    @pytest.mark.parametrize("case", add_user_cases)
    def test_add_user(self, case):
        """测试添加用户"""
        allure.dynamic.title(case["name"])
        allure.dynamic.severity(case.get("severity", "critical"))
        
        email = case['data'].get('email', 'unknown')
        with allure.step(f"发送添加用户请求 - 邮箱: {email}"):
            response = self.client.add_user(case["data"])
            allure.attach(str(case["data"]), "请求数据", allure.attachment_type.JSON)
        
        with allure.step(f"验证状态码: {case['expected_code']}"):
            assert response.status_code == case["expected_code"], \
                f"期望 {case['expected_code']}, 实际 {response.status_code}: {response.text}"
        
        # 记录创建的用户用于清理（仅在成功时）
        if response.status_code == 200:
            resp_data = response.json()
            user_id = resp_data.get("id") or resp_data.get("data", {}).get("id")
            if user_id:
                self.rollback_manager.record_user(user_id, email, case["data"].get("password", ""))
    
    @pytest.mark.parametrize("case", update_user_cases)
    def test_update_user(self, case):
        """测试更新用户"""
        allure.dynamic.title(case["name"])
        allure.dynamic.severity(case.get("severity", "normal"))
        
        user_id = case.get("user_id")
        created_user_id = None  # 记录是否创建了临时用户
        
        # 如果URL中有{user_id}占位符，先创建用户
        if user_id and "{" in str(user_id):
            with allure.step("自动创建测试用户"):
                temp_email = f"update_{uuid.uuid4().hex[:8]}@test.com"
                create_resp = self.client.add_user({
                    "name": f"UpdateUser_{uuid.uuid4().hex[:6]}",
                    "email": temp_email,
                    "password": "Test@123456"
                })
                if create_resp.status_code == 200:
                    resp_data = create_resp.json()
                    user_id = resp_data.get("id") or resp_data.get("data", {}).get("id")
                    if not user_id:
                        list_resp = self.client.get_users()
                        if list_resp.status_code == 200:
                            users = list_resp.json()
                            for u in users:
                                if u.get("email") == temp_email:
                                    user_id = u.get("id")
                                    break
                    created_user_id = user_id
        
        if not user_id:
            pytest.fail(f"无法获取有效的用户ID")
        
        # 保存原始数据用于回滚
        if created_user_id:
            original_resp = self.client.get_user(created_user_id)
            if original_resp.status_code == 200:
                self.rollback_manager.record_update("user", created_user_id, original_resp.json())
        
        with allure.step(f"更新用户ID: {user_id}"):
            response = self.client.update_user(str(user_id), case["data"])
        
        with allure.step(f"验证状态码: {case['expected_code']}"):
            assert response.status_code == case["expected_code"], \
                f"期望 {case['expected_code']}, 实际 {response.status_code}: {response.text}"
    
    @pytest.mark.parametrize("case", delete_user_cases)
    def test_delete_user(self, case):
        """测试删除用户"""
        allure.dynamic.title(case["name"])
        allure.dynamic.severity(case.get("severity", "critical"))
        
        user_id = case.get("user_id")
        setup = case.get("setup")
        created_user_id = None  # 记录是否创建了临时用户
        
        # 创建临时用户
        temp_email = f"delete_{uuid.uuid4().hex[:8]}@test.com"
        create_resp = self.client.add_user({
            "name": f"DeleteUser_{uuid.uuid4().hex[:6]}",
            "email": temp_email,
            "password": "Test@123456"
        })
        if create_resp.status_code == 200:
            resp_data = create_resp.json()
            user_id = resp_data.get("id") or resp_data.get("data", {}).get("id")
            if not user_id:
                list_resp = self.client.get_users()
                if list_resp.status_code == 200:
                    users = list_resp.json()
                    for u in users:
                        if u.get("email") == temp_email:
                            user_id = u.get("id")
                            break
            created_user_id = user_id
        
        # 如果有setup: create_and_delete，先删除用户
        if setup == "create_and_delete" and user_id:
            self.client.delete_user(str(user_id))
            created_user_id = None  # 已被删除，无需回滚
        
        if not user_id:
            pytest.fail(f"无法获取有效的用户ID")
        
        with allure.step(f"删除用户ID: {user_id}"):
            response = self.client.delete_user(str(user_id))
        
        with allure.step(f"验证状态码: {case['expected_code']}"):
            assert response.status_code == case["expected_code"], \
                f"期望 {case['expected_code']}, 实际 {response.status_code}: {response.text}"
        
        # 如果删除失败，记录用户用于清理；删除成功则不记录（已被删除）
        if response.status_code != 200 and created_user_id:
            self.rollback_manager.record_user(created_user_id, temp_email, "")
    
    @pytest.mark.parametrize("case", get_user_cases)
    def test_get_user(self, case, precreated_users):
        """测试获取用户"""
        global _query_user_index
        
        allure.dynamic.title(case["name"])
        allure.dynamic.severity(case.get("severity", "normal"))
        
        user_id = case.get("user_id")
        
        # 如果URL中有{user_id}占位符，优先使用预创建用户
        if user_id and "{" in str(user_id):
            # 尝试从预创建用户池获取 query_test 类型用户
            query_users = [u for u in precreated_users if u.get("template") == "query_test"]
            if query_users:
                # 轮询分配用户（避免每次都使用同一个）
                index = _query_user_index % len(query_users)
                target_user = query_users[index]
                user_id = target_user["user_id"]
                _query_user_index += 1
                allure.attach(f"使用预创建用户 #{index+1}: {target_user['email']} (ID: {user_id})", "用户来源", allure.attachment_type.TEXT)
            else:
                # 兜底：创建临时用户（回滚会清理，不会污染数据库）
                with allure.step("预创建用户池无可用用户，创建临时用户"):
                    temp_email = f"query_{uuid.uuid4().hex[:8]}@test.com"
                    create_resp = self.client.add_user({
                        "name": f"QueryUser_{uuid.uuid4().hex[:6]}",
                        "email": temp_email,
                        "password": "Test@123456"
                    })
                    if create_resp.status_code == 200:
                        user_id = create_resp.json().get("id")
                        if not user_id:
                            user_id = create_resp.json().get("data", {}).get("id")
                        # 记录到回滚管理器，session结束时会清理
                        self.rollback_manager.record_user(user_id, temp_email, "Test@123456")
                        allure.attach(f"临时用户ID: {user_id}", "用户来源", allure.attachment_type.TEXT)
                    else:
                        pytest.skip(f"无法创建测试用户: {create_resp.text}")
        
        with allure.step(f"获取用户信息"):
            if user_id:
                response = self.client.get_user(str(user_id))
            else:
                response = self.client.get_users()
        
        with allure.step(f"验证状态码: {case['expected_code']}"):
            assert response.status_code == case["expected_code"], \
                f"期望 {case['expected_code']}, 实际 {response.status_code}: {response.text}"
