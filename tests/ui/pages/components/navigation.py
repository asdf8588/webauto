# -*- coding: utf-8 -*-
"""
navigation.py - 通用导航组件

解决重复性代码维护问题：
所有页面复用同一个导航组件，只需要修改一次。
"""
import re


class NavigationComponent:
    """通用导航组件 - 所有页面复用"""
    
    def __init__(self, page):
        self.page = page
    
    def goto_home(self):
        """跳转到首页"""
        self.page.get_by_role("link", name=re.compile(r".*首页.*")).click()
    
    def goto_user_list(self):
        """跳转到用户列表"""
        # 精确匹配"用户列表"链接，避免匹配其他包含"用户"的链接
        self.page.get_by_role("link", name=re.compile(r".*用户列表.*")).click()
    
    def goto_login(self):
        """跳转到登录页"""
        self.page.get_by_role("link", name=re.compile(r".*登录.*")).click()
    
    def goto_register(self):
        """跳转到注册页"""
        self.page.get_by_role("link", name=re.compile(r".*注册.*")).click()
    
    def goto_add_user(self):
        """跳转到添加用户页"""
        self.page.get_by_role("link", name=re.compile(r".*创建.*|.*注册.*用户.*")).click()
    
    def goto_user_info(self):
        """跳转到查询用户页"""
        self.page.get_by_role("link", name=re.compile(r".*查询.*|.*用户.*信息.*")).click()
    
    def goto_update_password(self):
        """跳转到修改密码页"""
        self.page.get_by_role("link", name=re.compile(r".*修改.*密码.*")).click()
    
    def goto_update_user(self):
        """跳转到更新用户页"""
        self.page.get_by_role("link", name=re.compile(r".*更新.*|.*修改.*用户.*")).click()
    
    def logout(self):
        """退出登录"""
        self.page.get_by_role("button", name=re.compile(r".*退出.*")).click()