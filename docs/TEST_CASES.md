# 测试用例分类文档

## 一、测试用例总览

| 分类 | 测试文件 | 用例数 | 数据源 | 回滚机制 |
|------|----------|--------|--------|----------|
| **API 用户管理** | `tests/api/test_user.py` | 批量参数化 | YAML | 无（依赖固定用户） |
| **API 认证** | `tests/api/test_auth.py` | 批量参数化 | YAML | 无 |
| **API 密码管理** | `tests/api/test_password.py` | 批量参数化 | YAML | addfinalizer |
| **API 端到端** | `tests/api/test_e2e.py` | 批量参数化 | YAML | 无 |
| **注册登录全链路** | `tests/api/test_auth_flow.py` | 15 | 动态生成 | TransactionRollback ✓ |
| **UI 登录测试** | `tests/ui/test_login.py` | 5 | 固定数据 | 无 |
| **UI 导航测试** | `tests/ui/test_navigation.py` | 6 | 固定数据 | 无 |

---

## 二、问题分析

### 2.1 现有测试的问题

| 问题 | 现状 | 影响 |
|------|------|------|
| **数据硬编码** | 使用 `admin@example.com` 等固定用户 | 测试间相互干扰 |
| **回滚缺失** | 注册/更新后未清理 | 数据库脏数据累积 |
| **数据依赖** | 假设用户已存在 | 环境搭建复杂 |
| **并发风险** | 邮箱可能重复 | 并发测试失败 |

### 2.2 推荐方案对比

| 方案 | 优点 | 缺点 | 适用场景 |
|------|------|------|----------|
| **TransactionRollback（推荐）** | 自动回滚、数据隔离、简单实现 | 需要DELETE接口支持 | API 测试 |
| **addfinalizer** | 清理函数灵活 | 代码复杂 | 密码恢复等场景 |
| **数据准备（Setup）** | 测试数据可控 | 准备/清理代码多 | 复杂前置条件 |
| **测试数据库事务** | 完全隔离 | 需要数据库支持 | 单元测试 |

---

## 三、测试用例分类详解

### 3.1 API 测试类

#### A. 用户管理模块 (`test_user.py`)

```yaml
功能: 用户CRUD操作
数据驱动: data/user/*.yaml
回滚: 无（使用固定admin用户）
```

| 用例类别 | 测试方法 | 输入数据 | 预期结果 |
|----------|----------|----------|----------|
| **添加用户** | `test_add_user` | 注册参数（name/email/password） | 200成功/400失败 |
| **查询用户** | `test_get_user` | user_id 或空（列表） | 200返回数据/404不存在 |
| **更新用户** | `test_update_user` | user_id + 更新字段 | 200成功/400失败 |
| **删除用户** | `test_delete_user` | user_id | 200成功/404不存在 |

#### B. 认证模块 (`test_auth.py`)

```yaml
功能: 登录/登出
数据驱动: data/login/*.yaml
回滚: 无
```

| 用例类别 | 测试方法 | 输入数据 | 预期结果 |
|----------|----------|----------|----------|
| **登录成功** | `test_login` | email + password | 200 + token |
| **登录失败** | `test_login` | 错误密码/不存在用户 | 401/400 |
| **登出** | `test_logout` | token | 200成功 |

#### C. 密码管理模块 (`test_password.py`)

```yaml
功能: 修改密码
数据驱动: data/user/password.yaml
回滚: addfinalizer 恢复原密码
```

| 用例类别 | 测试方法 | 输入数据 | 预期结果 |
|----------|----------|----------|----------|
| **修改密码成功** | `test_update_password` | email + oldPassword + newPassword | 200成功 |
| **旧密码错误** | `test_update_password` | 错误旧密码 | 400失败 |
| **新密码为空** | `test_update_password` | 空新密码 | 400失败 |

#### D. 端到端模块 (`test_e2e.py`)

```yaml
功能: 多步骤业务流程
数据驱动: data/e2e.yaml
回滚: 无
```

| 用例类别 | 测试方法 | 流程步骤 |
|----------|----------|----------|
| **用户生命周期** | `test_e2e` | 注册 → 登录 → 查询 → 登出 |
| **认证流程** | `test_e2e` | 登录 → 查询用户列表 → 登出 |

#### E. 注册登录全链路 (`test_auth_flow.py`) ⭐推荐

```yaml
功能: 完整业务流程 + 事务回滚
数据源: 动态生成（唯一邮箱）
回滚: TransactionRollback 类
```

**核心 Fixtures：**

```python
registered_user    # 自动注册 → 自动清理
auth_token         # 注册 → 登录 → 返回token
rollback_manager   # 手动记录 → 测试后回滚
```

| 测试类 | 测试方法 | 功能 | 回滚 |
|--------|----------|------|------|
| **TestRegistration** | `test_register_success_complete_params` | 完整参数注册 | ✓ |
| | `test_register_success_minimal_params` | 最小参数注册 | ✓ |
| | `test_register_duplicate_email` | 重复邮箱注册失败 | ✓（依赖已注册用户） |
| **TestLogin** | `test_login_success_after_registration` | 注册后登录成功 | ✓ |
| | `test_login_wrong_password` | 错误密码登录失败 | ✓ |
| | `test_login_unregistered_email` | 未注册邮箱登录失败 | - |
| **TestAuthentication** | `test_query_with_auth_token` | 带Token查询成功 | ✓ |
| | `test_query_without_token` | 无Token查询失败 | - |
| | `test_get_user_detail` | 查询用户详情 | ✓ |
| **TestUpdateAndRollback** | `test_update_user_with_auto_rollback` | 更新+自动回滚 | ✓ |
| **TestConcurrencyAndIsolation** | `test_concurrent_registration_isolation[0-2]` | 并发注册隔离 | ✓ |
| | `test_multiple_users_independent_auth` | 多用户独立认证 | ✓ |
| **TestEndToEndFlow** | `test_full_flow_register_login_query` | 端到端全流程 | ✓ |

---

### 3.2 UI 测试类

#### A. 登录页面测试 (`test_login.py`)

```yaml
功能: 登录页面UI元素和交互
回滚: 无
```

| 测试方法 | 测试场景 | 预期结果 |
|----------|----------|----------|
| `test_login_success` | 正确凭据登录 | 跳转到首页 |
| `test_login_failure` | 错误密码登录 | 显示错误提示 |
| `test_email_input` | 邮箱输入框存在 | 可见 |
| `test_password_input` | 密码输入框存在 | 可见 |
| `test_login_button` | 登录按钮存在且可用 | 可见且启用 |

#### B. 导航测试 (`test_navigation.py`)

```yaml
功能: 页面导航和用户管理
回滚: 无
```

| 测试类 | 测试方法 | 场景 |
|--------|----------|------|
| **TestNavigation** | `test_home_page_elements` | 首页元素显示 |
| | `test_navigate_to_user_management` | 导航到用户管理 |
| **TestUserManagementUI** | `test_user_page_loads` | 用户管理页面加载 |
| | `test_user_table_displays` | 用户表格显示 |
| **TestLoginUI** | `test_login_fail_with_invalid_credentials` | 无效凭据登录失败 |
| **TestEndToEnd** | `test_complete_login_flow` | 完整登录到用户管理流程 |

---

## 四、运行命令

### 4.1 运行全部测试

```bash
# API 测试
pytest tests/api/ -v

# UI 测试
pytest tests/ui/ -v

# 所有测试
pytest tests/ -v
```

### 4.2 按类别运行

```bash
# 只运行注册登录全链路（带事务回滚）
pytest tests/api/test_auth_flow.py -v

# 只运行用户管理
pytest tests/api/test_user.py -v

# 只运行UI测试
pytest tests/ui/ -v -k "ui"
```

### 4.3 带 Allure 报告

```bash
pytest tests/ -v --alluredir=allure-results
allure serve allure-results
```

---

## 五、测试数据管理最佳实践

### 5.1 事务回滚模式（推荐）

```python
class TransactionRollback:
    """测试数据回滚管理器"""
    
    def record_user(self, user_id, email, password):
        """记录创建的用户"""
        
    def record_update(self, record_type, record_id, old_data):
        """记录更新的数据"""
        
    def rollback(self):
        """逆向回滚所有操作"""
```

### 5.2 Fixture 依赖链

```
registered_user (创建用户) 
    ↓
auth_token (登录获取Token)
    ↓
api_client (自动带Token)
```

### 5.3 数据隔离策略

| 场景 | 策略 | 实现 |
|------|------|------|
| 注册测试 | 动态生成唯一邮箱 | `f"test_{uuid}@example.com"` |
| 登录测试 | 依赖 registered_user | Fixture 传参 |
| 查询测试 | 使用已认证用户 | auth_token fixture |
| 更新测试 | 保存旧值+回滚 | rollback_manager |

---

## 六、测试运行结果（2026-04-22）

### 全链路测试 (test_auth_flow.py) ✅ 15/15 通过

```
15 passed in 8.66s
```

| 测试文件 | 通过 | 失败 |
|----------|------|------|
| test_auth_flow.py | 15 | 0 |
| test_auth.py | 6 | 0 |
| test_e2e.py | 2 | 0 |
| test_password.py | 1 | 0 |
| test_user.py | 18 | 0 |
| **总计** | **42** | **0** |

---

## 七、改进建议

### 7.1 短期（立即实施）

1. ✅ `test_auth_flow.py` 已实现事务回滚
2. 将 `test_user.py` 中的固定 admin 改为动态生成
3. 添加数据清理 fixture 到 conftest.py

### 7.2 中期（下一版本）

1. 为 `test_user.py` 添加 TransactionRollback
2. 为 `test_auth.py` 中的登出测试添加回滚
3. 统一使用 `registered_user` fixture

### 7.3 长期（架构优化）

1. 引入测试数据库（每个测试独立 DB）
2. 使用 pytest-db-session 管理事务
3. 添加数据工厂（Factory）模式

---

## 八、附录：测试文件结构

```
tests/
├── api/                          # API 测试
│   ├── __init__.py
│   ├── test_auth.py             # 认证测试（YAML驱动）
│   ├── test_auth_flow.py        # 全链路测试（事务回滚）⭐
│   ├── test_e2e.py              # 端到端测试（YAML驱动）
│   ├── test_password.py         # 密码管理测试
│   └── test_user.py             # 用户CRUD测试（YAML驱动）
│
├── ui/                          # UI 测试
│   ├── __init__.py
│   ├── conftest.py
│   ├── test_login.py            # 登录页面测试
│   ├── test_navigation.py      # 导航测试
│   ├── test_browser_lifecycle.py
│   └── pages/                   # Page Object 模型
│       ├── base_page.py
│       ├── home_page.py
│       ├── login_page.py
│       └── user_page.py
│
└── load.py                      # 负载测试（可选）
```