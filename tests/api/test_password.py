# -*- coding: utf-8 -*-
"""
密码修改模块测试
接口: PUT /users/password
"""
import pytest
import yaml
import os
import allure


DATA_DIR = os.path.join(os.path.dirname(__file__), "../../data/user")
with open(os.path.join(DATA_DIR, "password.yaml"), "r", encoding="utf-8") as f:
    password_cases = yaml.safe_load(f) or []


@allure.feature("密码管理模块")
class TestPasswordAPI:
    """密码修改接口测试"""

    @pytest.fixture(autouse=True)
    def setup(self, api_client, base_url, request):
        """每个测试前先登录获取token"""
        self.client = api_client
        self.base_url = base_url
        self.original_password = "123456"

        # 登录获取token
        response = self.client.login("admin@example.com", self.original_password)
        if response.status_code == 200:
            token = response.json().get("token")
            if token:
                self.client.set_token(token)

        # 使用request.addfinalizer确保测试后恢复密码
        def restore_password():
            try:
                import requests as req
                resp = req.put(
                    f"{self.base_url}/users/password",
                    json={
                        "email": "admin@example.com",
                        "oldPassword": "NewPass123",
                        "newPassword": self.original_password
                    }
                )
            except:
                pass

        request.addfinalizer(restore_password)

    @pytest.mark.parametrize("case", password_cases)
    def test_update_password(self, case):
        """测试修改密码"""
        allure.dynamic.title(case["name"])
        allure.dynamic.description(case["description"])
        allure.dynamic.severity("critical")

        with allure.step(f"修改密码 - 邮箱: {case['email']}"):
            response = self.client.update_password(
                email=case["email"],
                old_password=case["old_password"],
                new_password=case["new_password"]
            )
            allure.attach(str(case), "请求数据", allure.attachment_type.JSON)

        with allure.step(f"验证状态码: {case['expected']['status']}"):
            assert response.status_code == case["expected"]["status"], \
                f"期望 {case['expected']['status']}, 实际 {response.status_code}: {response.text}"

        if response.status_code == 200:
            allure.attach("密码修改成功", "验证结果", attachment_type=allure.attachment_type.TEXT)