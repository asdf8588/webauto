# conftest.py
# pytest 全局配置和 fixtures

import pytest
import requests
import os
from pathlib import Path

# 基础 URL 配置
BASE_URL = os.getenv('BASE_URL', 'http://localhost:8080')


@pytest.fixture(scope='session')
def base_url():
    """基础 URL"""
    return BASE_URL


@pytest.fixture(scope='session')
def api_client(base_url):
    """API 客户端"""
    class APIClient:
        def __init__(self, base_url):
            self.base_url = base_url
            self.session = requests.Session()
            self.token = None
        
        def set_token(self, token):
            self.token = token
        
        def request(self, method, path, **kwargs):
            url = f"{self.base_url}{path}"
            headers = kwargs.pop('headers', {})
            if self.token:
                headers['Authorization'] = f'Bearer {self.token}'
            headers.setdefault('Content-Type', 'application/json')
            
            response = self.session.request(method, url, headers=headers, **kwargs)
            return response
        
        def get(self, path, **kwargs):
            return self.request('GET', path, **kwargs)
        
        def post(self, path, **kwargs):
            return self.request('POST', path, **kwargs)
        
        def put(self, path, **kwargs):
            return self.request('PUT', path, **kwargs)
        
        def patch(self, path, **kwargs):
            return self.request('PATCH', path, **kwargs)
        
        def delete(self, path, **kwargs):
            return self.request('DELETE', path, **kwargs)
    
    return APIClient(base_url)


@pytest.fixture
def test_user():
    """测试用户数据"""
    import uuid
    return {
        'username': f'test_{uuid.uuid4().hex[:8]}',
        'password': 'Test123456',
        'email': f'test_{uuid.uuid4().hex[:8]}@example.com'
    }


@pytest.fixture
def auth_token(api_client, test_user):
    """获取认证 token"""
    # 注册用户
    api_client.post('/api/user/register', json=test_user)
    
    # 登录获取 token
    response = api_client.post('/api/user/login', json={
        'username': test_user['username'],
        'password': test_user['password']
    })
    
    if response.status_code == 200:
        data = response.json()
        token = data.get('token') or data.get('data', {}).get('token')
        if token:
            api_client.set_token(token)
    
    yield api_client
    
    # 清理：删除用户
    try:
        api_client.delete('/api/user/delete', json={'username': test_user['username']})
    except:
        pass


def pytest_configure(config):
    """pytest 配置钩子"""
    # 创建报告目录
    Path('reports').mkdir(exist_ok=True)
    Path('allure-results').mkdir(exist_ok=True)


def pytest_collection_modifyitems(config, items):
    """修改收集到的测试用例"""
    for item in items:
        # 根据测试文件路径自动添加标记
        if 'test_login' in item.nodeid:
            item.add_marker(pytest.mark.login)
        if 'test_user' in item.nodeid:
            item.add_marker(pytest.mark.user)
        if 'e2e' in item.nodeid:
            item.add_marker(pytest.mark.e2e)
