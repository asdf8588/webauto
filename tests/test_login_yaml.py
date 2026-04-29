"""
test_login_yaml.py - 登录测试（YAML 数据驱动）
"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pytest
import allure
from utils.data_loader import load_yaml
from ui.pages.login_page import LoginPage


def get_cases():
    return load_yaml("test_data/login_cases.yaml")


@pytest.mark.parametrize("case", get_cases())
@allure.feature("登录模块")
@allure.story("YAML数据驱动")
class TestLoginYaml:

    @pytest.fixture(autouse=True)
    def setup(self, shared_page, base_url):
        self.login_page = LoginPage(shared_page, base_url)

    def test_login(self, case):
        email = str(case.get("email") or "")
        password = str(case.get("password") or "")
        expect_type = str(case.get("expect_type") or "success")

        self.login_page.login(email, password)

        if expect_type == "success":
            self.login_page.expect_login_success()
        else:
            self.login_page.expect_login_failed()
