"""
ConfigLoader - 配置文件加载器

从YAML文件加载API配置，支持多环境切换
"""
import os
import yaml
from pathlib import Path
from typing import Dict, Any, Optional


class ConfigLoader:
    """API配置加载器"""

    def __init__(self, config_file: str = None):
        if config_file is None:
            project_root = Path(__file__).parent.parent
            config_file = project_root / "config" / "api_config.yaml"

        with open(config_file, 'r', encoding='utf-8') as f:
            self._config = yaml.safe_load(f)

        # 获取当前环境配置
        env = os.environ.get('API_ENV', self._config.get('default_env', 'dev'))
        self.env = env
        self.env_config = self._config.get('environments', {}).get(env, {})

    @property
    def base_url(self) -> str:
        return self.env_config.get('base_url', 'http://localhost:8080')

    @property
    def timeout(self) -> int:
        return self.env_config.get('timeout', 10)

    def get_test_user(self, name: str = 'normal') -> Dict[str, str]:
        """获取测试用户配置"""
        users = self._config.get('test_users', {})
        return users.get(name, {})


# 全局实例
_config: Optional[ConfigLoader] = None


def get_config() -> ConfigLoader:
    global _config
    if _config is None:
        _config = ConfigLoader()
    return _config
