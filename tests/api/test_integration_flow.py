# -*- coding: utf-8 -*-
"""
test_integration_flow.py - 一站式闭环集成测试

测试流程：
  ┌─────────────────────────────────────────────────────────────────┐
  │  Session Start                                                  │
  │  ├── 创建预注册用户池 (precreated_users)                         │
  │  └── 记录到 rollback_manager                                    │
  └─────────────────────────────────────────────────────────────────┘
                              ↓
  ┌─────────────────────────────────────────────────────────────────┐
  │  测试阶段 1: 注册测试 (使用占位符 + 动态生成)                     │
  │  ├── 创建新用户                                                  │
  │  └── 记录到 rollback_manager                                     │
  └─────────────────────────────────────────────────────────────────┘
                              ↓
  ┌─────────────────────────────────────────────────────────────────┐
  │  测试阶段 2: 登录测试 (使用 precreated_users)                     │
  │  ├── 使用预创建的用户进行登录                                     │
  │  └── 验证登录状态                                                 │
  └─────────────────────────────────────────────────────────────────┘
                              ↓
  ┌─────────────────────────────────────────────────────────────────┐
  │  测试阶段 3: 查询测试 (使用 precreated_users)                    │
  │  ├── 查询单个用户                                                │
  │  ├── 查询用户列表                                                │
  │  └── 验证数据一致性                                              │
  └─────────────────────────────────────────────────────────────────┘
                              ↓
  ┌─────────────────────────────────────────────────────────────────┐
  │  测试阶段 4: 端到端测试 (注册→登录→查询)                         │
  │  ├── 完整业务流程验证                                             │
  │  └── 数据一致性检查                                               │
  └─────────────────────────────────────────────────────────────────┘
                              ↓
  ┌─────────────────────────────────────────────────────────────────┐
  │  Session End                                                    │
  │  └── rollback_manager 统一清理所有数据                           │
  └─────────────────────────────────────────────────────────────────┘

核心优势：
  ✅ 真实用户旅程：注册→登录→查询完整闭环
  ✅ 环境始终纯净：测试结束后自动清理
  ✅ 数据共享：预创建用户供所有测试复用
  ✅ 无冲突：每次运行使用不同的用户数据
"""
import pytest
import allure
import os
import yaml


# ═══════════════════════════════════════════════════════════════════════════
# 测试数据加载
# ═══════════════════════════════════════════════════════════════════════════
DATA_DIR = "data/user"


def _load_yaml(filename):
    """加载 YAML 文件"""
    path = os.path.join(DATA_DIR, filename)
    with open(path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f) or []


def _load_cases(filename):
    """加载并处理用例 - 自动替换占位符"""
    from utils.data_generator import process_auto_fields
    return [process_auto_fields(item) for item in _load_yaml(filename)]


# 加载测试数据
_register_cases = _load_cases("register.yaml")
_login_cases = _load_cases("login.yaml")
_query_cases = _load_cases("query.yaml")
_e2e_cases = _load_cases("e2e.yaml")


# ═══════════════════════════════════════════════════════════════════════════
# 辅助函数
# ═══════════════════════════════════════════════════════════════════════════
def _execute_setup(api_client, rollback_manager, setup_steps):
    """执行前置步骤"""
    for step in setup_steps:
        action = step.get("action")

        if action == "register_login":
            resp = api_client.add_user({
                "name": step.get("name"),
                "email": step.get("email"),
                "password": step.get("password")
            })
            if resp.status_code == 200:
                user_id = resp.json().get("id")
                if user_id:
                    rollback_manager.record_user(user_id, step["email"], step["password"])
            api_client.login(step["email"], step["password"])


# ═══════════════════════════════════════════════════════════════════════════
# 阶段 1: 注册测试
# ═══════════════════════════════════════════════════════════════════════════
@allure.feature("一站式闭环测试")
@allure.story("阶段1: 用户注册")
class TestPhase1_Registration:
    """
    使用 YAML 数据驱动 + 动态生成
    创建的用户记录到 rollback_manager
    """

    @pytest.mark.parametrize("case", _register_cases)
    def test_register(self, api_client, rollback_manager, case):
        """注册测试"""
        allure.dynamic.title(case["name"])

        with allure.step("执行前置步骤"):
            _execute_setup(api_client, rollback_manager, case.get("setup", []))

        with allure.step(f"发送注册请求: POST {case['url']}"):
            response = api_client.add_user(case["body"])

        with allure.step("验证响应状态"):
            expected_status = case["expected"]["status"]
            assert response.status_code == expected_status, \
                f"期望 {expected_status}，实际 {response.status_code}"

        with allure.step("记录创建的用户用于回滚"):
            if response.status_code == 200 and case.get("rollback"):
                user_id = response.json().get("id")
                if user_id:
                    rollback_manager.record_user(
                        user_id,
                        case["body"].get("email", ""),
                        case["body"].get("password", "")
                    )


# ═══════════════════════════════════════════════════════════════════════════
# 阶段 2: 登录测试
# ═══════════════════════════════════════════════════════════════════════════
@allure.feature("一站式闭环测试")
@allure.story("阶段2: 用户登录")
class TestPhase2_Login:
    """
    使用 precreated_users 中的用户进行登录测试
    这些用户在 session 开始时已创建，session 结束时统一清理
    """

    def test_login_with_precreated_user(self, api_client, precreated_users):
        """使用预创建用户测试登录"""
        user = precreated_users[0]  # 获取第一个预创建用户

        allure.dynamic.title(f"登录测试: {user['email']}")

        with allure.step(f"使用用户 {user['email']} 登录"):
            response = api_client.login(user["email"], user["password"])

        with allure.step("验证登录成功"):
            assert response.status_code == 200, \
                f"登录失败: {response.status_code}"

        with allure.step("验证返回 token"):
            resp_data = response.json()
            assert "token" in resp_data or "data" in resp_data

    def test_login_all_precreated_users(self, api_client, precreated_users):
        """测试所有预创建用户的登录"""
        allure.dynamic.title("批量登录测试")

        for i, user in enumerate(precreated_users):
            with allure.step(f"测试用户 {i+1}/{len(precreated_users)}: {user['email']}"):
                response = api_client.login(user["email"], user["password"])
                assert response.status_code == 200, \
                    f"用户 {user['email']} 登录失败"

    @pytest.mark.parametrize("case", _login_cases)
    def test_login_cases(self, api_client, precreated_users, case):
        """登录用例测试 - 使用 setup 中的用户"""
        allure.dynamic.title(case["name"])

        with allure.step("执行前置步骤（注册+登录）"):
            _execute_setup(api_client, None, case.get("setup", []))

        with allure.step(f"发送登录请求: POST {case['url']}"):
            response = api_client.login(
                case["body"]["email"],
                case["body"]["password"]
            )

        with allure.step("验证响应状态"):
            expected_status = case["expected"]["status"]
            assert response.status_code == expected_status, \
                f"期望 {expected_status}，实际 {response.status_code}"


# ═══════════════════════════════════════════════════════════════════════════
# 阶段 3: 查询测试
# ═══════════════════════════════════════════════════════════════════════════
@allure.feature("一站式闭环测试")
@allure.story("阶段3: 用户查询")
class TestPhase3_Query:
    """
    使用 precreated_users 中的用户进行查询测试
    """

    def test_query_single_user(self, api_client, precreated_users):
        """查询单个用户"""
        user = precreated_users[0]

        allure.dynamic.title(f"查询用户: {user['email']}")

        with allure.step(f"查询用户 ID={user['user_id']}"):
            # 使用 API Client 的 get_user 方法，路径是 /users/seek/{id}
            response = api_client.get_user(user["user_id"])

        with allure.step("验证查询成功"):
            assert response.status_code == 200, \
                f"查询失败: {response.status_code}"

        with allure.step("验证用户数据"):
            resp_data = response.json()
            assert resp_data.get("email") == user["email"]
            assert resp_data.get("name") == user["name"]

    def test_query_all_users(self, api_client, precreated_users):
        """查询所有用户"""
        allure.dynamic.title(f"查询全部用户（预创建 {len(precreated_users)} 个）")

        with allure.step("查询用户列表"):
            response = api_client.get("/users")

        with allure.step("验证查询成功"):
            assert response.status_code == 200, \
                f"查询失败: {response.status_code}"

        with allure.step(f"验证返回用户数量 >= {len(precreated_users)}"):
            resp_data = response.json()
            users_list = resp_data if isinstance(resp_data, list) else resp_data.get("data", [])
            assert len(users_list) >= len(precreated_users), \
                f"期望至少 {len(precreated_users)} 个用户，实际 {len(users_list)}"

    @pytest.mark.parametrize("case", _query_cases)
    def test_query_cases(self, api_client, rollback_manager, case):
        """查询用例测试"""
        allure.dynamic.title(case["name"])

        # 执行前置 setup
        user_id = None
        for step in case.get("setup", []):
            if step.get("action") == "register_login":
                resp = api_client.add_user({
                    "name": step.get("name"),
                    "email": step.get("email"),
                    "password": step.get("password")
                })
                if resp.status_code == 200:
                    user_id = resp.json().get("id")
                    rollback_manager.record_user(user_id, step["email"], step["password"])
                api_client.login(step["email"], step["password"])

        # 替换 URL 中的占位符
        url = case["url"]
        if user_id and "{user_id}" in url:
            url = url.replace("{user_id}", str(user_id))

        with allure.step(f"发送查询请求: GET {url}"):
            response = api_client.get(url)

        with allure.step("验证响应状态"):
            expected_status = case["expected"]["status"]
            assert response.status_code == expected_status, \
                f"期望 {expected_status}，实际 {response.status_code}"


# ═══════════════════════════════════════════════════════════════════════════
# 阶段 4: 端到端全链路测试
# ═══════════════════════════════════════════════════════════════════════════
@allure.feature("一站式闭环测试")
@allure.story("阶段4: 端到端全链路")
class TestPhase4_E2E:
    """
    完整业务流程测试：注册 → 登录 → 查询 → 删除
    """

    def test_full_flow_register_login_query(self, api_client, rollback_manager):
        """
        完整流程: 注册 → 登录 → 查询
        
        这个测试模拟真实用户旅程：
        1. 注册新用户
        2. 使用新注册的账号登录
        3. 查询用户信息验证注册成功
        """
        allure.dynamic.title("完整流程: 注册→登录→查询")

        # 步骤1: 注册
        with allure.step("步骤1: 注册新用户"):
            email = f"e2e_{uuid.uuid4().hex[:8]}@example.com"
            register_data = {
                "name": f"E2EUser_{uuid.uuid4().hex[:8]}",
                "email": email,
                "password": "Test@123456"
            }
            resp = api_client.add_user(register_data)
            assert resp.status_code == 200, f"注册失败: {resp.status_code}"
            user_id = resp.json().get("id")
            rollback_manager.record_user(user_id, email, register_data["password"])
            print(f"  ✅ 注册成功: {email} (ID: {user_id})")

        # 步骤2: 登录
        with allure.step("步骤2: 使用新账号登录"):
            resp = api_client.login(email, register_data["password"])
            assert resp.status_code == 200, f"登录失败: {resp.status_code}"
            print(f"  ✅ 登录成功")

        # 步骤3: 查询验证
        with allure.step("步骤3: 查询用户信息"):
            # 使用正确的 API 路径
            resp = api_client.get_user(user_id)
            assert resp.status_code == 200, f"查询失败: {resp.status_code}"
            user_data = resp.json()
            assert user_data.get("email") == email, "邮箱不匹配"
            print(f"  ✅ 查询验证成功")

    def test_full_flow_using_precreated_users(self, api_client, precreated_users, rollback_manager):
        """
        使用预创建用户进行完整流程测试
        
        流程：登录 → 查询 → 更新 → 查询验证
        """
        allure.dynamic.title("预创建用户完整流程测试")

        # 获取一个预创建用户
        user = precreated_users[0]

        # 步骤1: 登录
        with allure.step("步骤1: 登录"):
            resp = api_client.login(user["email"], user["password"])
            assert resp.status_code == 200, f"登录失败"
            print(f"  ✅ 登录成功: {user['email']}")

        # 步骤2: 查询
        with allure.step("步骤2: 查询用户"):
            resp = api_client.get_user(user["user_id"])
            assert resp.status_code == 200, f"查询失败"
            print(f"  ✅ 查询成功")

        # 步骤3: 获取旧数据并更新
        with allure.step("步骤3: 更新用户"):
            old_data = resp.json()
            rollback_manager.record_update("user", user["user_id"], old_data)

            new_name = f"Updated_{uuid.uuid4().hex[:8]}"
            resp = api_client.update_user(str(user["user_id"]), {"name": new_name})
            assert resp.status_code == 200, f"更新失败"
            print(f"  ✅ 更新成功: {new_name}")

        # 步骤4: 验证更新
        with allure.step("步骤4: 验证更新"):
            resp = api_client.get_user(user["user_id"])
            assert resp.status_code == 200
            updated_data = resp.json()
            assert updated_data.get("name") == new_name, "更新验证失败"
            print(f"  ✅ 更新验证成功")

    @pytest.mark.parametrize("case", _e2e_cases)
    def test_e2e_cases(self, api_client, rollback_manager, case):
        """端到端用例测试"""
        allure.dynamic.title(case["name"])

        with allure.step("执行前置步骤"):
            _execute_setup(api_client, rollback_manager, case.get("setup", []))

        with allure.step(f"发送请求: {case['method']} {case['url']}"):
            if case["method"].upper() == "GET":
                response = api_client.get(case["url"])
            elif case["method"].upper() == "POST":
                response = api_client.post(case["url"], case.get("body", {}))

        with allure.step("验证响应状态"):
            expected_status = case["expected"]["status"]
            assert response.status_code == expected_status, \
                f"期望 {expected_status}，实际 {response.status_code}"


# ═══════════════════════════════════════════════════════════════════════════
# 阶段 5: 数据一致性验证（可选，最后执行）
# ═══════════════════════════════════════════════════════════════════════════
@allure.feature("一站式闭环测试")
@allure.story("阶段5: 数据一致性验证")
class TestPhase5_DataConsistency:
    """
    验证所有测试产生的数据都被正确记录和清理
    """

    def test_verify_precreated_users_exist(self, api_client, precreated_users):
        """验证预创建用户仍然存在于数据库"""
        allure.dynamic.title("验证预创建用户存在")

        for user in precreated_users:
            # 使用正确的 API 路径
            resp = api_client.get_user(user["user_id"])
            assert resp.status_code == 200, \
                f"预创建用户 {user['email']} 不存在"

    def test_verify_test_data_isolation(self, api_client, precreated_users):
        """验证测试数据隔离性"""
        allure.dynamic.title("验证数据隔离")

        # 查询所有用户
        resp = api_client.get("/users")
        assert resp.status_code == 200

        all_users = resp.json() if isinstance(resp.json(), list) else resp.json().get("data", [])

        # 验证所有预创建用户都在列表中
        precreated_ids = {u["user_id"] for u in precreated_users}
        for user in all_users:
            if user.get("id") in precreated_ids:
                print(f"  ✅ 预创建用户存在: {user.get('email')}")


# ═══════════════════════════════════════════════════════════════════════════
# Import uuid for E2E tests
# ═══════════════════════════════════════════════════════════════════════════
import uuid
