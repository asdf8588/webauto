# -*- coding: utf-8 -*-
"""自动生成的测试 - 来自 OpenAPI 规范"""

import pytest
import requests

BASE_URL = "http://localhost:8080"


class TestOpenAPI:

    def test_auto_login_200(self):
        """用户登录 - 200"""
        response = requests.post(
            f"{BASE_URL}/users/login",
            json={"email": "test@example.com", "password": "123456"},
            headers={"Content-Type": "application/json"}
        )
        assert response.status_code == 200

    def test_auto_login_400(self):
        """用户登录 - 400"""
        response = requests.post(
            f"{BASE_URL}/users/login",
            json={"email": "test@example.com", "password": "123456"},
            headers={"Content-Type": "application/json"}
        )
        assert response.status_code == 400

    def test_auto_register_200(self):
        """用户注册 - 200"""
        response = requests.post(
            f"{BASE_URL}/users/add",
            json={},
            headers={"Content-Type": "application/json"}
        )
        assert response.status_code == 200

    def test_auto_register_400(self):
        """用户注册 - 400"""
        response = requests.post(
            f"{BASE_URL}/users/add",
            json={},
            headers={"Content-Type": "application/json"}
        )
        assert response.status_code == 400
