# -*- coding: utf-8 -*-
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


    def test_auto_login_200(self):
        """用户登录 - 200"""
        url = f"{BASE_URL}/users/login"
        headers = {"Content-Type": "application/json"}
        data = {"email": "test@example.com", "password": "123456"}

        response = requests.post(url, json=data, headers=headers)

        assert response.status_code == 200, \
            f"期望状态码 {expected_status}，实际 {response.status_code}"

        # 验证响应格式
        try:
            result = response.json()
            assert "status" in result, "响应缺少 status 字段"
            assert result["status"] == 200
        except ValueError:
            pytest.fail("响应不是有效的 JSON")

    def test_auto_login_400(self):
        """用户登录 - 400"""
        url = f"{BASE_URL}/users/login"
        headers = {"Content-Type": "application/json"}
        data = {"email": "test@example.com", "password": "123456"}

        response = requests.post(url, json=data, headers=headers)

        assert response.status_code == 400, \
            f"期望状态码 {expected_status}，实际 {response.status_code}"

        # 验证响应格式
        try:
            result = response.json()
            assert "status" in result, "响应缺少 status 字段"
            assert result["status"] == 400
        except ValueError:
            pytest.fail("响应不是有效的 JSON")

    def test_auto_register_200(self):
        """用户注册 - 200"""
        url = f"{BASE_URL}/users/add"
        headers = {"Content-Type": "application/json"}
        data = {}

        response = requests.post(url, json=data, headers=headers)

        assert response.status_code == 200, \
            f"期望状态码 {expected_status}，实际 {response.status_code}"

        # 验证响应格式
        try:
            result = response.json()
            assert "status" in result, "响应缺少 status 字段"
            assert result["status"] == 200
        except ValueError:
            pytest.fail("响应不是有效的 JSON")

    def test_auto_register_400(self):
        """用户注册 - 400"""
        url = f"{BASE_URL}/users/add"
        headers = {"Content-Type": "application/json"}
        data = {}

        response = requests.post(url, json=data, headers=headers)

        assert response.status_code == 400, \
            f"期望状态码 {expected_status}，实际 {response.status_code}"

        # 验证响应格式
        try:
            result = response.json()
            assert "status" in result, "响应缺少 status 字段"
            assert result["status"] == 400
        except ValueError:
            pytest.fail("响应不是有效的 JSON")

# ============ 使用说明 ============
# 1. 生成这些测试: python openapi_validator.py --generate
# 2. 启动 Mock 服务器: python openapi_validator.py --serve
# 3. 运行测试: pytest tests/api/test_generated_from_openapi.py -v
#
# 这个文件是自动生成的，修改后会被覆盖
# 如需自定义测试，请在 tests/api/ 目录创建新的测试文件
