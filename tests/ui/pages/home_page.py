# -*- coding: utf-8 -*-
"""
home_page.py - 首页页面对象

包含导航组件复用
"""
import re
from .base_page import BasePage
from .components import NavigationComponent


class HomePage(BasePage):
    """首页页面对象"""
    
    URL = "/index.html"
    
    # ─── 定位器 ─────────────────────────────────────────────────────────────
    TITLE = ("heading", r".*用户.*")
    WELCOME_TEXT = ("paragraph", r".*Spring.*")
    
    def __init__(self, page, base_url: str = "http://localhost:8080"):
        super().__init__(page)
        self.base_url = base_url
        self.url = f"{base_url}{self.URL}"
        self.nav = NavigationComponent(page)
    
    def open(self):
        self.visit(self.url)
    
    def goto_home(self):
        """跳转到首页"""
        self.nav.goto_home()
    
    def goto_user_list(self):
        """跳转到用户列表"""
        self.nav.goto_user_list()
    
    def goto_add_user(self):
        """跳转到添加用户"""
        self.nav.goto_add_user()
    
    def goto_user_info(self):
        """跳转到查询用户"""
        self.nav.goto_user_info()
    
    def goto_update_password(self):
        """跳转到修改密码"""
        self.nav.goto_update_password()
    
    def goto_update_user(self):
        """跳转到更新用户"""
        self.nav.goto_update_user()
    
    def logout(self):
        """退出登录"""
        self.nav.logout()
    
    def wait_for_dashboard(self):
        """等待仪表盘加载"""
        self.wait_for_selector("body")
        self.page.wait_for_load_state("networkidle")
    
    # ─── 测试用例需要的方法 ─────────────────────────────────────────────
    def get_heading(self):
        """获取页面标题（测试用例需要）"""
        return self.page.get_by_role("heading", name=re.compile(r".*用户.*"))
    
    def get_user_list_link(self):
        """获取用户列表链接（测试用例需要）"""
        return self.page.get_by_role("link", name=re.compile(r".*用户列表.*"))
    
    def navigate_to_user_list(self):
        """导航到用户列表（测试用例需要）"""
        self.nav.goto_user_list()
