# -*- coding: utf-8 -*-
"""
导航和用户管理UI测试
"""
import pytest
import allure
from .pages.home_page import HomePage
from .pages.user_page import UserPage
from .pages.login_page import LoginPage


def _login(page, base_url):
    """内部辅助：登录管理员"""
    lp = LoginPage(page, base_url)
    lp.login("admin@example.com", "123456")


@allure.feature("导航功能")
class TestNavigation:

    @allure.title("首页元素显示")
    @allure.severity("normal")
    def test_home_page_elements(self, shared_page, base_url):
        _login(shared_page, base_url)
        home = HomePage(shared_page, base_url)
        shared_page.goto(f"{base_url}/index.html")
        assert home.get_heading().is_visible()
        assert home.get_user_list_link().is_visible()

    @allure.title("导航到用户管理页面")
    @allure.severity("critical")
    def test_navigate_to_user_management(self, shared_page, base_url):
        _login(shared_page, base_url)
        home = HomePage(shared_page, base_url)
        shared_page.goto(f"{base_url}/index.html")
        home.navigate_to_user_list()
        assert "users.html" in shared_page.url


@allure.feature("用户管理页面")
class TestUserManagementUI:

    @allure.title("用户管理页面加载")
    @allure.severity("normal")
    def test_user_page_loads(self, shared_page, base_url):
        _login(shared_page, base_url)
        shared_page.goto(f"{base_url}/users.html")
        heading = shared_page.get_by_role("heading", name="👥 用户列表")
        assert heading.is_visible()

    @allure.title("用户表格显示")
    @allure.severity("normal")
    def test_user_table_displays(self, shared_page, base_url):
        _login(shared_page, base_url)
        shared_page.goto(f"{base_url}/users.html")
        # 等待表格加载完成
        shared_page.wait_for_selector("table", state="visible", timeout=10000)
        user_page = UserPage(shared_page, base_url)
        assert user_page.get_user_table().is_visible()
        rows = user_page.get_user_rows()
        allure.attach(f"表格行数: {rows.count()}", "验证结果", attachment_type=allure.attachment_type.TEXT)


@allure.feature("登录功能")
class TestLoginUI:

    @allure.title("登录失败测试 - 无效凭据")
    @allure.severity("normal")
    def test_login_fail_with_invalid_credentials(self, shared_page, base_url):
        """故意使用错误凭据测试登录失败场景"""
        lp = LoginPage(shared_page, base_url)
        shared_page.goto(f"{base_url}/login.html")
        lp.input_email("wrong@example.com")
        lp.click_login()  # 不输入密码或输入错误密码
        # 预期：登录失败，当前URL仍是登录页（没有跳转）
        # 检查页面是否有错误提示或URL没有跳转到成功页面
        import time
        time.sleep(0.5)  # 等待UI响应
        current_url = shared_page.url
        # 方法1: URL 没有跳转（仍在登录页）
        # 方法2: 检查是否有错误提示元素（更健壮）
        error_visible = False
        try:
            error_visible = shared_page.get_by_text("用户").first.is_visible() or \
                           shared_page.get_by_text("错误").first.is_visible() or \
                           shared_page.get_by_text("失败").first.is_visible()
        except:
            pass
        # 最终验证：URL没有跳转到首页
        assert "/login" in current_url or error_visible, \
            f"登录失败应该停留在登录页，当前URL: {current_url}"


@allure.feature("端到端测试")
class TestEndToEnd:

    @allure.title("完整登录流程")
    @allure.severity("blocker")
    def test_complete_login_flow(self, shared_page, base_url):
        """从登录到用户管理的完整流程"""
        lp = LoginPage(shared_page, base_url)
        lp.login("admin@example.com", "123456")
        lp.expect_login_success()
        # 直接跳转，提示框在新页面不存在

        home = HomePage(shared_page, base_url)
        shared_page.goto(f"{base_url}/index.html")
        home.navigate_to_user_list()

        user_page = UserPage(shared_page, base_url)
        # 等待表格加载完成
        shared_page.wait_for_selector("table", state="visible", timeout=10000)
        assert user_page.get_user_table().is_visible()
        allure.attach("用户管理页面加载成功", "验证结果", attachment_type=allure.attachment_type.TEXT)
