"""
API Client - HTTP请求封装

封装GET/POST/PUT/PATCH/DELETE等HTTP方法及业务方法
"""
import requests
import allure
from typing import Dict, Any, Optional


class APIClient:
    """HTTP API客户端"""

    def __init__(self, base_url: str, timeout: int = 10):
        self.base_url = base_url.rstrip('/')
        self.timeout = timeout
        self.session = requests.Session()
        self.session.headers.update({
            "Content-Type": "application/json",
            "Accept": "application/json"
        })

    def set_token(self, token: str):
        """设置认证Token"""
        self.session.headers.update({"Authorization": f"Bearer {token}"})

    def clear_token(self):
        """清除认证Token"""
        self.session.headers.pop("Authorization", None)

    # ─────────────────────────────────────────────────────────────────────────
    # 认证相关方法
    # ─────────────────────────────────────────────────────────────────────────
    def login(self, email: str, password: str) -> requests.Response:
        """登录接口"""
        return self.post("/users/login", json={"email": email, "password": password})

    def update_password(self, email: str, old_password: str, new_password: str) -> requests.Response:
        """修改密码（参数：邮箱 + 旧密码 + 新密码）"""
        return self.put("/users/password", json={
            "email": email,
            "oldPassword": old_password,
            "newPassword": new_password
        })

    # ─────────────────────────────────────────────────────────────────────────
    # 用户管理相关方法
    # ─────────────────────────────────────────────────────────────────────────
    def add_user(self, data: Dict[str, Any]) -> requests.Response:
        """添加用户"""
        return self.post("/users/add", json=data)

    def get_user(self, user_id: int) -> requests.Response:
        """获取单个用户"""
        return self.get(f"/users/seek/{user_id}")

    def get_users(self, **kwargs) -> requests.Response:
        """获取用户列表"""
        return self.get("/users", params=kwargs)

    def check_user(self, user_id: int) -> requests.Response:
        """检查用户是否存在"""
        return self.get(f"/users/check/{user_id}")

    def get_allowed_methods(self) -> requests.Response:
        """获取允许的 HTTP 方法"""
        return self.get("/users/allowed")

    def update_user(self, user_id: str, data: Dict[str, Any]) -> requests.Response:
        """更新用户"""
        return self.put(f"/users/{user_id}", json=data)

    def delete_user(self, user_id: str) -> requests.Response:
        """删除用户"""
        return self.delete(f"/users/{user_id}")

    # ─────────────────────────────────────────────────────────────────────────
    # 基础 HTTP 方法
    # ─────────────────────────────────────────────────────────────────────────
    def _build_url(self, path: str) -> str:
        """构建完整URL"""
        path = path.lstrip('/') if isinstance(path, str) else ""
        return f"{self.base_url}/{path}"

    def _log_request(self, method: str, url: str, **kwargs):
        """记录请求到Allure"""
        body = kwargs.get('json') or kwargs.get('data') or {}
        allure.attach(
            f"URL: {url}\nMethod: {method}\nBody: {body}",
            name="Request",
            attachment_type=allure.attachment_type.TEXT
        )

    def _log_response(self, response: requests.Response):
        """记录响应到Allure"""
        try:
            body = response.text[:500] if response.text else "(empty)"
        except Exception:
            body = "(unable to read)"
        allure.attach(
            f"Status: {response.status_code}\nBody: {body}",
            name="Response",
            attachment_type=allure.attachment_type.TEXT
        )

    def request(self, method: str, path: str, **kwargs) -> requests.Response:
        """发送HTTP请求"""
        url = self._build_url(path)
        kwargs.setdefault('timeout', self.timeout)
        self._log_request(method, url, **kwargs)
        response = self.session.request(method, url, **kwargs)
        self._log_response(response)
        return response

    def get(self, path: str, **kwargs) -> requests.Response:
        return self.request("GET", path, **kwargs)

    def post(self, path: str, **kwargs) -> requests.Response:
        return self.request("POST", path, **kwargs)

    def put(self, path: str, **kwargs) -> requests.Response:
        return self.request("PUT", path, **kwargs)

    def patch(self, path: str, **kwargs) -> requests.Response:
        return self.request("PATCH", path, **kwargs)

    def delete(self, path: str, **kwargs) -> requests.Response:
        return self.request("DELETE", path, **kwargs)

    def options(self, path: str, **kwargs) -> requests.Response:
        return self.request("OPTIONS", path, **kwargs)

    def close(self):
        self.session.close()