# -*- coding: utf-8 -*-
"""
动态数据生成器 - 静态用例 + 动态数据

核心概念：
  - YAML 用例写占位符 __AUTO_UUID__, __AUTO_EMAIL__
  - 代码加载用例时自动替换为唯一真实值
  - 每次运行测试数据唯一，测试后可回滚清理

支持的占位符：
  __AUTO_UUID__      -> 8位随机字符串 (abc123de)  
  __AUTO_EMAIL__     -> auto_abc123de@example.com
  __AUTO_TIMESTAMP__ -> 毫秒时间戳
  __AUTO_INT__       -> 随机整数
  ${SAME}            -> 在同一用例中保持相同的值（需配合钩子）
"""
import uuid
import time
import re
from typing import Any, Dict


def gen_uuid() -> str:
    """生成8位唯一ID"""
    return uuid.uuid4().hex[:8]


def gen_email(suffix: str = "example.com") -> str:
    """生成唯一邮箱"""
    unique_id = gen_uuid()
    return f"auto_{unique_id}@{suffix}"


def gen_timestamp() -> str:
    """生成时间戳"""
    return str(int(time.time() * 1000))


def gen_int(min_val: int = 1, max_val: int = 99999) -> int:
    """生成随机整数"""
    import random
    return random.randint(min_val, max_val)


def _replace_placeholders(value: str, generated: Dict[str, str]) -> Any:
    """
    替换单个值中的占位符
    
    处理逻辑：
    1. __AUTO_UUID__ -> 生成新uuid
    2. __AUTO_EMAIL__ -> 生成新email
    3. ${SAME:key} -> 复用已生成的值
    """
    if not isinstance(value, str):
        return value
    
    # 替换 ${SAME:key} - 复用之前生成的值
    same_pattern = r'\$\{SAME:(\w+)\}'
    same_matches = re.findall(same_pattern, value)
    for key in same_matches:
        if key in generated:
            value = value.replace(f'${{SAME:{key}}}', generated[key])
    
    # 替换 __AUTO_UUID__
    if '__AUTO_UUID__' in value:
        new_uuid = gen_uuid()
        generated['uuid'] = new_uuid  # 保存以便复用
        value = value.replace('__AUTO_UUID__', new_uuid)
    
    # 替换 __AUTO_EMAIL__
    if '__AUTO_EMAIL__' in value:
        new_email = gen_email()
        generated['email'] = new_email
        value = value.replace('__AUTO_EMAIL__', new_email)
    
    # 替换 __AUTO_TIMESTAMP__
    if '__AUTO_TIMESTAMP__' in value:
        value = value.replace('__AUTO_TIMESTAMP__', gen_timestamp())
    
    # 替换 __AUTO_INT__
    if '__AUTO_INT__' in value:
        value = value.replace('__AUTO_INT__', str(gen_int()))
    
    return value


def process_auto_fields(data: Any, generated: Dict[str, str] = None) -> Any:
    """
    递归处理数据中的占位符，自动替换为真实值
    
    支持的占位符格式:
    - __AUTO_UUID__     -> 8位随机字符串
    - __AUTO_EMAIL__    -> 唯一邮箱
    - ${SAME:uuid}       -> 复用同一用例中生成的uuid
    - ${SAME:email}      -> 复用同一用例中生成的email
    """
    if generated is None:
        generated = {}
    
    if isinstance(data, dict):
        result = {}
        for key, value in data.items():
            result[key] = process_auto_fields(value, generated)
        return result
    elif isinstance(data, list):
        return [process_auto_fields(item, generated) for item in data]
    elif isinstance(data, str):
        return _replace_placeholders(data, generated)
    else:
        return data


def auto_value(field_type: str) -> Any:
    """根据字段类型生成对应值"""
    generators = {
        "uuid": gen_uuid,
        "email": gen_email,
        "timestamp": gen_timestamp,
        "int": gen_int,
    }
    return generators.get(field_type, gen_uuid)()
