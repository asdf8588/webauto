# -*- coding: utf-8 -*-
"""
登录UI测试 - 核心场景
"""
import pytest
import allure
from .pages.login_page import LoginPage


@allure.feature("登录页面")
@allure.story("登录功能UI验证")
class TestLoginUI:
    """登录页面UI测试"""

    @pytest.fixture
    def login_page(self, shared_page, base_url):
        lp = LoginPage(shared_page, base_url)
        lp.open()
        return lp

    @allure.title("登录成功 - 跳转到首页")
    @allure.severity("critical")
    def test_login_success(self, login_page):
        login_page.login("test2@example.com", "123456")
        login_page.expect_login_success()

    @allure.title("登录失败 - 显示错误提示")
    @allure.severity("normal")
    def test_login_failure(self, login_page):
        login_page.login("test2@example.com", "wrongpass")
        login_page.expect_login_failed()


@allure.feature("登录页面")
@allure.story("页面元素验证")
class TestLoginElements:
    """登录页面元素测试"""

    @allure.title("邮箱输入框存在")
    @allure.severity("critical")
    def test_email_input(self, shared_page, base_url):
        lp = LoginPage(shared_page, base_url)
        lp.open()
        lp.expect_visible(lp.EMAIL_INPUT)

    @allure.title("密码输入框存在")
    @allure.severity("critical")
    def test_password_input(self, shared_page, base_url):
        lp = LoginPage(shared_page, base_url)
        lp.open()
        lp.expect_visible(lp.PASSWORD_INPUT)

    @allure.title("登录按钮存在")
    @allure.severity("critical")
    def test_login_button(self, shared_page, base_url):
        lp = LoginPage(shared_page, base_url)
        lp.open()
        lp.expect_enabled(lp.SUBMIT_BTN)
