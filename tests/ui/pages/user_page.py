# -*- coding: utf-8 -*-
"""
user_page.py - 用户列表页面

基于无障碍树生成的定位器
"""
import re
from .base_page import BasePage


class UserPage(BasePage):
    """用户列表页面"""

    URL = "/users.html"

    # ─── 无障碍树定位器 ────────────────────────────────────────────────────
    # 从 a11y_users_parsed.json 生成
    TITLE = ("heading", r".*用户.*")
    USER_NAME = ("cell", r"test")      # 用户名单元格
    DELETE_BTN = ("button", r".*删除.*")

    # 搜索相关
    SEARCH_INPUT = ("textbox", r".*ID.*")
    SEARCH_BTN = ("button", r".*查询.*")

    def __init__(self, page, base_url: str = "http://localhost:8080"):
        super().__init__(page)
        self.base_url = base_url
        self.url = f"{base_url}{self.URL}"

    def open(self):
        self.visit(self.url)

    def search_by_id(self, user_id: str):
        self.fill(self.SEARCH_INPUT, user_id)
        self.click(self.SEARCH_BTN)

    def delete_user(self, user_name: str):
        """删除指定用户"""
        # 使用正则匹配包含用户名的行
        row = self.page.locator("tr").filter(has=self.page.locator(f"text=/{user_name}/"))
        delete_btn = row.locator("button").filter(has_text="删除")
        delete_btn.click()
    
    # ─── 测试用例需要的方法 ─────────────────────────────────────────────
    def get_user_table(self):
        """获取用户表格（测试用例需要）"""
        return self.page.locator("table")
    
    def get_user_rows(self):
        """获取用户表格行（测试用例需要）"""
        return self.page.locator("table tbody tr")
