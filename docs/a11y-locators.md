# 无障碍树定位器指南

## 1. 生成无障碍树

```bash
# 生成所有页面
python get_accessibility_tree.py

# 生成指定页面
python get_accessibility_tree.py -u /login.html

# 查看可用页面
python get_accessibility_tree.py --list
```

## 2. 定位器模式

从 `a11y/a11y_*.json` 中找到元素后，按以下规则转换为代码：

### 模式 1: get_by_role + 正则 (推荐)

```python
# 原始快照:
# - heading "用户列表" [level=1]

# 转换代码:
page.get_by_role("heading", name=re.compile(r"用户列表"))
```

### 模式 2: 模糊匹配

```python
# 更灵活的匹配
page.get_by_role("link", name=re.compile(r".*登录.*"))
```

### 模式 3: 表单元素

```python
# 原始快照:
# - textbox "请输入邮箱"

# 转换代码:
page.get_by_role("textbox", name=re.compile(r".*邮箱.*"))
# 或更精确
page.get_by_label(re.compile(r"邮箱"))
```

### 模式 4: CSS 备选

```python
# 复杂情况使用 CSS
page.locator("#infoBox")
page.locator("button[type='submit']")
```

## 3. Page Object 使用

```python
# tests/ui/pages/login_page.py
import re
from .base_page import BasePage

class LoginPage(BasePage):
    # 定义定位器 (role, pattern)
    EMAIL_INPUT = ("textbox", r".*邮箱.*")
    PASSWORD_INPUT = ("textbox", r".*密码.*")
    SUBMIT_BTN = ("button", r".*登录.*")
    
    # 使用
    def login(self, email, password):
        self.fill(self.EMAIL_INPUT, email)
        self.fill(self.PASSWORD_INPUT, password)
        self.click(self.SUBMIT_BTN)
```

## 4. 常用 Role 对照

| Role | 含义 | 示例 |
|------|------|------|
| `heading` | 标题 | h1, h2 |
| `link` | 链接 | a |
| `button` | 按钮 | button |
| `textbox` | 输入框 | input, textarea |
| `checkbox` | 复选框 | input[type=checkbox] |
| `radio` | 单选按钮 | input[type=radio] |
| `menuitem` | 菜单项 | menu 中的元素 |
| `menu` | 菜单 | nav, menu |
| `row` | 表格行 | tr |
| `cell` | 单元格 | td |
| `paragraph` | 段落 | p |

## 5. 常见定位器速查

```python
# 标题
page.get_by_role("heading", name="用户列表")

# 登录按钮
page.get_by_role("button", name=re.compile(r"登录", re.i))

# 输入框 (多种方式)
page.get_by_role("textbox", name=re.compile(r"邮箱"))
page.get_by_label("邮箱")
page.get_by_placeholder("请输入邮箱")

# 链接
page.get_by_role("link", name="注册")
page.get_by_role("link", name=re.compile(r"登录"))
```

## 6. 调试技巧

```python
# 打印当前页面的无障碍树
snapshot = page.locator("body").aria_snapshot()
print(snapshot)

# 检查元素是否存在
elem = page.get_by_role("button", name=re.compile(r"登录"))
print(elem.count())  # > 0 表示存在
```
