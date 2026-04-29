# -*- coding: utf-8 -*-
"""
base_page.py - 页面对象基类

封装 Playwright 公共操作，所有 Page 类继承此类。
改进：使用 Playwright 内置 expect() web-first 断言
支持智能定位器：(role, pattern) → get_by_role(role, name=re.compile(pattern))
"""
import re
from typing import Union, Tuple
from playwright.sync_api import Page, expect, Locator


class BasePage:
    """页面对象基类 - 使用 Playwright 官方最佳实践"""

    def __init__(self, page: Page):
        self.page = page

    # ─── 页面导航 ───────────────────────────────────────────────────────────
    def visit(self, url: str):
        """打开页面"""
        self.page.goto(url, wait_until="domcontentloaded")

    def goto(self, url: str):
        """打开页面（兼容旧代码）"""
        self.page.goto(url)
        self.page.wait_for_load_state("networkidle")

    # ─── 元素操作 ───────────────────────────────────────────────────────────
    def locator(self, selector: str) -> Locator:
        """CSS 选择器定位"""
        return self.page.locator(selector)

    def get_by_role(self, role: str, **kwargs) -> Locator:
        """get_by_role定位"""
        return self.page.get_by_role(role, **kwargs)

    def get_by_placeholder(self, placeholder: str) -> Locator:
        return self.page.get_by_placeholder(placeholder)

    def get_by_label(self, label: str) -> Locator:
        return self.page.get_by_label(label)

    def get(self, locator: Union[str, Tuple[str, str]]) -> Locator:
        """
        智能定位器，支持：
        - 元组 ("role", r"pattern") → get_by_role(role, name=re.compile(pattern))
        - 元组 ("css", "selector") → locator(selector)
        - 字符串 → locator(selector)
        
        示例：
          get(("textbox", r".*邮箱.*"))  → page.get_by_role("textbox", name=re.compile(r".*邮箱.*"))
          get(("css", "#infoBox"))        → page.locator("#infoBox")
          get("button.submit")            → page.locator("button.submit")
        """
        if isinstance(locator, tuple):
            loc_type, value = locator
            if loc_type == "css":
                return self.page.locator(value)
            else:
                # role + regex pattern
                return self.page.get_by_role(loc_type, name=re.compile(value))
        # 普通字符串，CSS选择器
        return self.page.locator(locator)

    def fill(self, locator: Union[str, Tuple], text: str):
        """填写输入框"""
        self.get(locator).fill(text)

    def type_text(self, locator: Union[str, Tuple], text: str, delay: int = 30):
        """逐字输入"""
        self.get(locator).type(text, delay=delay)

    def click(self, locator: Union[str, Tuple]):
        """点击元素"""
        self.get(locator).click()

    def wait_for_url(self, url: str, timeout: int = 30000):
        self.page.wait_for_url(url, timeout=timeout)

    def wait_for_selector(self, selector: str, timeout: int = 30000):
        self.page.wait_for_selector(selector, timeout=timeout)

    # ─── Web-First 断言 (Playwright 官方推荐) ───────────────────────────────
    def expect_visible(self, locator: Union[str, Tuple], timeout: float = 5000):
        """断言元素可见 - 自动等待"""
        expect(self.get(locator)).to_be_visible(timeout=timeout)

    def expect_hidden(self, locator: Union[str, Tuple], timeout: float = 5000):
        """断言元素隐藏"""
        expect(self.get(locator)).to_be_hidden(timeout=timeout)

    def expect_text(self, locator: Union[str, Tuple], text: str, timeout: float = 5000):
        """断言元素文本内容"""
        expect(self.get(locator)).to_have_text(text, timeout=timeout)

    def expect_enabled(self, locator: Union[str, Tuple], timeout: float = 5000):
        """断言元素可点击"""
        expect(self.get(locator)).to_be_enabled(timeout=timeout)

    def expect_value(self, locator: Union[str, Tuple], value: str, timeout: float = 5000):
        """断言输入框的值"""
        expect(self.get(locator)).to_have_value(value, timeout=timeout)

    # ─── 工具方法 ──────────────────────────────────────────────────────────
    def get_text(self, locator: Union[str, Tuple]) -> str:
        """获取元素文本"""
        return self.get(locator).inner_text()

    def disable_html5_validation(self):
        """
        给表单加 novalidate，关闭浏览器原生校验。
        点击提交按钮不会被 HTML5 拦截，所有用例都能执行到底。
        """
        self.page.evaluate(
            '() => { const f = document.querySelector("form"); if(f) f.setAttribute("novalidate",""); }'
        )

    def screenshot(self, name: str = "screenshot"):
        """截图"""
        self.page.screenshot(path=f"{name}.png")
