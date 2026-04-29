# -*- coding: utf-8 -*-
"""
test_login_excel.py - 登录 UI 测试（Excel 数据驱动）

企业级测试逻辑：
  - expect_type="success" → 预期成功，实际成功=PASSED，实际失败=FAILED
  - expect_type="error"   → 预期失败，实际失败=XFAIL，实际成功=XPASSED

改进：使用 web-first 断言 expect_xxx() 替代手动判断
"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pytest
import allure
from utils.data_loader import load_excel
from ui.pages.login_page import LoginPage


def get_cases():
    """从 Excel 加载用例，返回用例列表"""
    data = load_excel("test_data/login_cases.xlsx")
    for cases in data.values():
        return cases
    return []


@allure.feature("登录模块")
@allure.story("UI自动化")
class TestLogin:

    @pytest.fixture(autouse=True)
    def setup(self, shared_page, base_url):
        self.login_page = LoginPage(shared_page, base_url)

    @pytest.mark.parametrize("case", get_cases())
    def test_login(self, case):
        """
        数据驱动登录测试 - 使用 Playwright expect 断言
        """
        case_id = str(case.get("case_id") or "")
        desc = str(case.get("desc") or "")
        email = str(case.get("email") or "") if case.get("email") else ""
        password = str(case.get("password") or "") if case.get("password") else ""
        expect_type = str(case.get("expect_type") or "success")

        allure.dynamic.title(f"[{case_id}] {desc}")

        # ── 执行登录（绕过 HTML5 校验，让后端处理）────────────────────────
        self.login_page.login(email, password)

        # ── 验证结果 ────────────────────────────────────────────────────────
        if expect_type == "success":
            self.login_page.expect_login_success()
        else:
            self.login_page.expect_login_failed()
