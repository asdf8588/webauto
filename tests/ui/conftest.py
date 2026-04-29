# -*- coding: utf-8 -*-
"""
tests/ui/conftest.py - UI测试专用配置

三级Fixture架构：
  session 级: playwright 驱动（只启动一次）
       ↓
  module 级: browser_context（每个模块一个上下文）
       ↓
  function 级: page（每个测试独立页面）

核心思路：同一个 browser，每个测试开一个新 page
"""
import pytest


# 基础URL配置
BASE_URL = "http://localhost:8080"


@pytest.fixture(scope="session")
def base_url():
    """返回基础URL（session级，与 pytest-base-url 插件兼容）"""
    return BASE_URL
