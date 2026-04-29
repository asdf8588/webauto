# -*- coding: utf-8 -*-
"""验证浏览器是否在测试间保持复用"""
import pytest
import allure


@allure.feature("浏览器复用验证")
class TestBrowserReuse:
    """验证同一个浏览器实例在不同测试间保持打开"""

    _browser_instances = []

    @allure.title("测试1：记录浏览器ID")
    def test_1_record_browser_id(self, browser, shared_page, base_url):
        test_id = id(browser)
        TestBrowserReuse._browser_instances.append(test_id)
        allure.attach(f"浏览器ID: {test_id}", "测试1")
        shared_page.goto(f"{base_url}/login.html")
        shared_page.wait_for_load_state("load")

    @allure.title("测试2：验证浏览器ID相同")
    def test_2_verify_same_browser_id(self, browser, shared_page, base_url):
        test_id = id(browser)
        TestBrowserReuse._browser_instances.append(test_id)
        allure.attach(f"浏览器ID: {test_id}", "测试2")
        allure.attach(f"历史ID列表: {TestBrowserReuse._browser_instances}", "所有测试的浏览器ID")
        assert TestBrowserReuse._browser_instances[0] == test_id, \
            f"浏览器不是同一个！测试1: {TestBrowserReuse._browser_instances[0]}, 测试2: {test_id}"
        shared_page.goto(f"{base_url}/login.html")
        shared_page.wait_for_load_state("load")

    @allure.title("测试3：再次验证浏览器ID")
    def test_3_verify_still_same_browser(self, browser, shared_page, base_url):
        test_id = id(browser)
        TestBrowserReuse._browser_instances.append(test_id)
        allure.attach(f"浏览器ID: {test_id}", "测试3")
        allure.attach(f"所有ID: {TestBrowserReuse._browser_instances}", "三个测试的浏览器ID")
        assert len(set(TestBrowserReuse._browser_instances)) == 1, \
            f"浏览器ID不唯一！{TestBrowserReuse._browser_instances}"
        shared_page.goto(f"{base_url}/login.html")
        shared_page.wait_for_load_state("load")
