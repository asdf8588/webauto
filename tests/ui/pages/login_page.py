# -*- coding: utf-8 -*-
"""
login_page.py - 登录页面对象

基于无障碍树生成的定位器，支持正则匹配
"""
import re
from .base_page import BasePage


class LoginPage(BasePage):
    """登录页面"""

    URL = "/login.html"

    # ─── 无障碍树定位器 ────────────────────────────────────────────────────
    # 格式: ("role", r"pattern") → page.get_by_role(role, name=re.compile(pattern))
    # 从 a11y_login_parsed.json 生成
    EMAIL_INPUT = ("textbox", r".*邮箱.*")
    PASSWORD_INPUT = ("textbox", r".*密码.*")
    SUBMIT_BTN = ("button", r".*登录.*")
    BACK_LINK = ("link", r".*返回.*")

    # 断言元素 (CSS备选)
    SUCCESS_BOX = ("css", "#infoBox")
    ERROR_MSG = ("css", "#msg")

    def __init__(self, page, base_url: str = "http://localhost:8080"):
        super().__init__(page)
        self.base_url = base_url
        self.url = f"{base_url}{self.URL}"

    # ─── 页面操作 ────────────────────────────────────────────────────────
    def open(self):
        self.visit(self.url)

    def goto_login_page(self):
        self.visit(self.url)

    def input_email(self, text: str):
        el = self.get(self.EMAIL_INPUT)
        el.clear()
        if text:
            el.type(text, delay=10)

    def input_password(self, text: str):
        el = self.get(self.PASSWORD_INPUT)
        el.clear()
        if text:
            el.type(text, delay=10)

    def click_login(self):
        self.get(self.SUBMIT_BTN).click()

    def click_back(self):
        self.get(self.BACK_LINK).click()

    def login(self, email: str, password: str):
        """完整登录流程"""
        self.open()
        self.input_email(email)
        self.input_password(password)
        self.disable_html5_validation()
        self.click_login()

    # ─── Web-First 断言 ──────────────────────────────────────────────────
    def expect_login_success(self, timeout: float = 8000):
        self.expect_visible(self.SUCCESS_BOX, timeout=timeout)

    def expect_login_failed(self, timeout: float = 5000):
        self.expect_visible(self.ERROR_MSG, timeout=timeout)

    def expect_error_text(self, expected_text: str, timeout: float = 5000):
        self.expect_text(self.ERROR_MSG, expected_text, timeout=timeout)

    # ─── 兼容旧代码 ───────────────────────────────────────────────────────
    def get_email_input(self):
        return self.get(self.EMAIL_INPUT)

    def get_password_input(self):
        return self.get(self.PASSWORD_INPUT)

    def get_login_button(self):
        return self.get(self.SUBMIT_BTN)

    def is_login_success(self) -> bool:
        try:
            self.expect_visible(self.SUCCESS_BOX, timeout=1000)
            return True
        except Exception:
            return False

    def is_login_failed(self) -> bool:
        try:
            self.expect_visible(self.ERROR_MSG, timeout=1000)
            return True
        except Exception:
            return False

    def get_error_text(self) -> str:
        return self.get_text(self.ERROR_MSG)
