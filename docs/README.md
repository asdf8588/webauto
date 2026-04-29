# Web 自动化测试框架

## 一、项目整体架构

```
webauto/
├── a11y/                         # 无障碍树JSON文件目录
│   ├── a11y_index.json
│   └── a11y_login.json
├── allure-report/                # Allure报告目录（一键生成）
├── allure-results/               # Allure测试结果数据
├── config/                       # 配置文件
├── data/                         # 测试数据（Excel、YAML格式）
│   ├── login/
│   ├── user/
│   └── e2e.yaml
├── docs/                         # 文档目录
├── logs/                         # 日志目录
├── test_data/                    # 测试数据备份
├── tests/                        # 测试代码目录
│   ├── api/                     # API测试（按模块分）
│   │   ├── test_auth.py         # 登录认证
│   │   ├── test_user.py         # 用户管理
│   │   └── test_password.py     # 密码修改
│   └── ui/                      # UI测试（POM模式）
│       ├── pages/               # 页面对象类
│       │   ├── base_page.py     # 基础页面类
│       │   ├── components/      # 通用组件
│       │   │   └── navigation.py  # 导航组件
│       │   ├── login_page.py
│       │   └── user_page.py
│       ├── test_login.py        # 登录模块测试
│       ├── test_user.py         # 用户模块测试
│       └── test_e2e.py          # 端到端测试
├── utils/                        # 工具类
│   ├── data_loader.py           # 数据加载器
│   └── api_client.py            # API客户端
├── conftest.py                   # 全局pytest配置
├── main.py                       # 主运行文件（一键生成报告）
├── get_accessibility_tree.py     # 生成无障碍树
├── show_trace.py                 # 打开Trace Viewer
├── pytest.ini                    # pytest配置
└── pytest_main.ini               # 主测试运行配置
```

---

## 二、核心设计理念

### 1. API测试 - 数据驱动

```python
# 数据与代码分离，YAML/Excel外部化测试数据
# @pytest.mark.parametrize 参数化
# Allure 动态装饰器
# Fixtures 集中管理
```

### 2. UI测试 - POM模式

```python
# pages/ 与 tests/ 分离
# BasePage 基类封装公共方法
# 元素选择器集中管理（基于无障碍树）
# Web-first expect() 断言
# 无状态设计，支持并行执行
```

### 3. 三级Fixture架构

```
session 级: playwright 驱动（只启动一次）
     ↓
module 级: browser_context（每个模块一个上下文）
     ↓
function 级: page（每个测试独立页面）
```

核心思路：**同一个 browser，每个测试开一个新 page**

---

## 三、快速开始

```bash
# 运行所有测试
python main.py

# 仅运行UI测试
pytest tests/ui/ -v

# 仅运行API测试
pytest tests/api/ -v

# 生成无障碍树
python get_accessibility_tree.py

# 打开Trace Viewer
python show_trace.py

# 查看测试报告
allure open allure-report
```

---

## 四、无障碍树与智能定位器

### 4.1 生成无障碍树

```bash
# 生成所有页面
python get_accessibility_tree.py

# 生成指定页面
python get_accessibility_tree.py -u /login.html

# 列出可用页面
python get_accessibility_tree.py --list
```

### 4.2 定位器模式

```python
# 原始快照 (a11y_login.json):
# - textbox "请输入邮箱"
# - textbox "请输入密码"
# - button "登录"

# 转换代码 (使用正则):
page.get_by_role("textbox", name=re.compile(r".*邮箱.*"))
page.get_by_role("textbox", name=re.compile(r".*密码.*"))
page.get_by_role("button", name=re.compile(r".*登录.*"))
```

### 4.3 Page Object 使用

```python
# tests/ui/pages/login_page.py
import re
from .base_page import BasePage

class LoginPage(BasePage):
    # 定位器常量: ("role", r"pattern")
    EMAIL_INPUT = ("textbox", r".*邮箱.*")
    PASSWORD_INPUT = ("textbox", r".*密码.*")
    SUBMIT_BTN = ("button", r".*登录.*")
    
    def login(self, email, password):
        self.fill(self.EMAIL_INPUT, email)
        self.fill(self.PASSWORD_INPUT, password)
        self.click(self.SUBMIT_BTN)
```

### 4.4 常用 Role 对照

| Role | 含义 | 示例 |
|------|------|------|
| `heading` | 标题 | h1, h2 |
| `link` | 链接 | a |
| `button` | 按钮 | button |
| `textbox` | 输入框 | input, textarea |
| `checkbox` | 复选框 | input[type=checkbox] |
| `menuitem` | 菜单项 | menu 中的元素 |
| `row` | 表格行 | tr |

---

## 五、端到端测试

```python
import pytest
import allure
from .pages.login_page import LoginPage
from .pages.home_page import HomePage

@allure.feature("端到端测试")
@allure.story("完整业务流程")
class TestE2E:
    """端到端测试 - 验证关键用户场景"""
    
    @pytest.fixture(autouse=True)
    def setup(self, page, page_navigate):
        self.page = page
        self.login_page = LoginPage(page)
        self.home_page = HomePage(page)
    
    def test_complete_user_flow(self):
        """完整用户流程：登录 -> 查看用户 -> 退出"""
        # 1. 登录
        self.login_page.goto(self.base_url + "/login.html")
        self.login_page.login("admin", "123456")
        
        # 2. 验证跳转首页
        self.home_page.wait_for_dashboard()
        
        # 3. 导航到用户管理
        self.home_page.nav.goto_user_list()
```

---

## 六、组件化设计

### 解决重复性代码维护问题

没有组件化时，每个 Page 类都要重复写导航代码：

```python
# ❌ 重复代码，维护噩梦
class LoginPage:
    def goto_home(self):
        self.page.locator("nav a:has-text('首页')").click()

class UserListPage:
    def goto_home(self):
        self.page.locator("nav a:has-text('首页')").click()  # 重复！
```

使用组件化后：

```python
# ✅ 组件化，只需要修改一次
# tests/ui/pages/components/navigation.py
class NavigationComponent:
    """通用导航组件 - 所有页面复用"""
    
    def __init__(self, page):
        self.page = page
    
    def goto_home(self):
        self.page.locator("nav a:has-text('首页')").click()
    
    def goto_user_list(self):
        self.page.locator("nav a:has-text('用户管理')").click()

# 使用
class LoginPage(BasePage):
    def __init__(self, page):
        super().__init__(page)
        self.nav = NavigationComponent(page)
    
    def some_action(self):
        self.nav.goto_home()  # 复用导航组件
```

---

## 七、提示框处理策略

提示框可能需要点击确定按钮，也可能只出现一个提示框消息。

- 如果有需要确认的提示框 → UI测试点击确定按钮
- 如果只是消息提示 → 直接进入新页面

```python
class BasePage:
    def handle_alert(self, action="accept", timeout=5000):
        """处理提示框
        
        Args:
            action: "accept" 接受/确定, "dismiss" 拒绝/取消
        """
        def handle_dialog(dialog):
            if action == "accept":
                dialog.accept()
            else:
                dialog.dismiss()
        
        self.page.on("dialog", handle_dialog)
```

---

## 八、测试金字塔策略

```
         /\
        /  \         UI测试 (10%)
       /----\        端到端验证核心流程
      /      \
     /--------\      API/集成测试 (20%)
    /  集成   \      模块间接口验证
   /   API     \
  /------------\
 /  单元测试   \    单元测试 (70%)
/    (70%)     \    基础功能验证
----------------
```

**测试策略：**
- **UI测试 (10%)**：验证关键用户场景，比如成功跳转、错误提示可见性。核心流程跑通即可，边界条件交给API。
- **API/集成测试 (20%)**：模块间接口验证
- **单元测试 (70%)**：基础功能验证

---

## 九、测试类结构

```python
@allure.feature("登录模块")
@allure.story("UI自动化")
class TestLogin:
    
    @pytest.fixture(autouse=True)
    def setup(self, page, page_navigate):
        """每个测试创建独立的LoginPage对象"""
        self.login_page = LoginPage(page)
        self.login_page.goto(page_navigate + "/login.html")
    
    @pytest.mark.parametrize("case", get_cases())
    def test_login(self, case):
        """参数化测试"""
        self.login_page.login(case["email"], case["password"])
        
        if case["expected"] == "success":
            assert self.login_page.is_success_visible()
        else:
            assert self.login_page.is_error_visible()
```

---

## 十、质量指标

Allure 报告注入质量指标：

| 指标 | 公式 | 说明 |
|------|------|------|
| 功能通过率 | Passed / (Total - Skipped - Expected) | 软件满足需求的比例 |
| 测试通过率 | Passed / Total | 用例执行通过的比例 |
| 测试稳定性 | Passed / (Passed + Failed + Broken) | 测试脚本健壮性 |
| 缺陷检出率 | Failed / Total | 本次测试发现缺陷的能力 |

---

## 十一、技术栈

| 类型 | 工具 | 说明 |
|------|------|------|
| 测试框架 | pytest | Python测试框架 |
| API客户端 | requests | HTTP请求封装 |
| UI自动化 | Playwright | 现代化浏览器自动化 |
| 数据驱动 | YAML/Excel | 测试数据外部化 |
| 报告工具 | Allure | 测试报告生成 |
| 断言 | Playwright expect | web-first断言 |

---

## 十二、参考文档

- [Playwright 官方 POM 文档](https://playwright.dev/docs/pom)
- [Playwright POM 最佳实践](https://www.techlistic.com/2026/02/playwright-page-object-model-pom-best.html)
- [pytest 官方文档](https://docs.pytest.org/)
- [Allure 测试报告](https://docs.qameta.io/allure/)
