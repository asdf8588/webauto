# -*- coding: utf-8 -*-
"""
统一测试用例加载器 - TestCaseLoader

自动扫描 test_cases/ 目录，加载所有 YAML 用例文件。
支持占位符自动替换：${AUTO_UUID}, ${AUTO_EMAIL}, ${SAME:key}
"""
import os
import yaml
import uuid
import copy
from pathlib import Path
from typing import List, Dict, Any, Optional


class CaseLoader:
    """统一测试用例加载器"""

    def __init__(self, data_dir: str = None):
        if data_dir is None:
            project_root = Path(__file__).parent.parent
            data_dir = project_root / "test_cases"
        self.data_dir = Path(data_dir)
        self._cache = {}

    def load_all(self) -> Dict[str, List[Dict[str, Any]]]:
        """加载所有测试用例，按模块分组"""
        if self._cache:
            return self._cache

        result = {}
        for yaml_file in self.data_dir.glob("*.yaml"):
            if yaml_file.name == "README.md":
                continue
            module_name = yaml_file.stem  # 文件名作为模块名
            cases = self.load_module(module_name)
            result[module_name] = cases

        self._cache = result
        return result

    def load_module(self, module: str) -> List[Dict[str, Any]]:
        """加载指定模块的测试用例"""
        file_path = self.data_dir / f"{module}.yaml"
        if not file_path.exists():
            return []

        with open(file_path, "r", encoding="utf-8") as f:
            cases = yaml.safe_load(f) or []
            return cases

    def get_all_cases(self) -> List[Dict[str, Any]]:
        """获取所有测试用例（扁平列表）"""
        all_modules = self.load_all()
        result = []
        for module, cases in all_modules.items():
            for case in cases:
                case_copy = copy.deepcopy(case)
                case_copy["_module"] = module
                result.append(case_copy)
        return result

    @staticmethod
    def resolve_case(case: Dict[str, Any]) -> Dict[str, Any]:
        """
        解析用例中的占位符：
        - ${AUTO_UUID} → 唯一UUID
        - ${AUTO_EMAIL} → 唯一邮箱
        - ${SAME:key} → 同一用例内的相同值
        """
        import time

        resolved = copy.deepcopy(case)
        generated = {}
        ts = str(int(time.time() * 1000))

        def replace_value(value):
            if isinstance(value, str):
                # 替换 ${AUTO_UUID}
                if "${AUTO_UUID}" in value:
                    if "${AUTO_UUID}" not in generated:
                        generated["${AUTO_UUID}"] = f"{ts}_{uuid.uuid4().hex[:8]}"
                    value = value.replace("${AUTO_UUID}", generated["${AUTO_UUID}"])

                # 替换 ${AUTO_EMAIL}
                if "${AUTO_EMAIL}" in value:
                    if "${AUTO_EMAIL}" not in generated:
                        generated["${AUTO_EMAIL}"] = f"test_{ts}_{uuid.uuid4().hex[:6]}@example.com"
                    value = value.replace("${AUTO_EMAIL}", generated["${AUTO_EMAIL}"])

                # 替换 ${SAME:key}
                if "${SAME:" in value:
                    start = value.find("${SAME:")
                    end = value.find("}", start)
                    if end != -1:
                        key = value[start + 7 : end]
                        same_key = f"${{SAME:{key}}}"
                        if same_key not in generated:
                            generated[same_key] = f"{ts}_{uuid.uuid4().hex[:6]}@example.com"
                        value = value.replace(same_key, generated[same_key])

                return value
            elif isinstance(value, dict):
                return {k: replace_value(v) for k, v in value.items()}
            elif isinstance(value, list):
                return [replace_value(item) for item in value]
            return value

        # 处理 body
        if "body" in resolved:
            resolved["body"] = replace_value(resolved["body"])

        # 处理 url
        if "url" in resolved:
            resolved["url"] = replace_value(resolved["url"])

        # 处理 setup
        if "setup" in resolved:
            resolved["setup"] = replace_value(resolved["setup"])

        return resolved

    def get_statistics(self) -> Dict[str, int]:
        """获取测试用例统计"""
        all_modules = self.load_all()
        stats = {}
        total = 0
        for module, cases in all_modules.items():
            count = len(cases)
            stats[module] = count
            total += count
        stats["_total"] = total
        return stats


# ═══════════════════════════════════════════════════════════════════════════
# 全局实例
# ═══════════════════════════════════════════════════════════════════════════
_loader = None


def get_loader() -> CaseLoader:
    """获取全局加载器实例"""
    global _loader
    if _loader is None:
        _loader = CaseLoader()
    return _loader


def load_cases(module: str = None) -> Any:
    """便捷加载函数"""
    loader = get_loader()
    if module:
        return loader.load_module(module)
    return loader.get_all_cases()


# ═══════════════════════════════════════════════════════════════════════════
# CLI 工具
# ═══════════════════════════════════════════════════════════════════════════
if __name__ == "__main__":
    loader = TestCaseLoader()

    print("\n" + "=" * 60)
    print("[TEST PLATFORM] Unified Test Case Statistics")
    print("=" * 60)

    stats = loader.get_statistics()
    print("\n各模块用例数量:")
    for module, count in sorted(stats.items()):
        if module != "_total":
            print(f"  {module:12s}: {count} 条")

    print(f"\n{'总计':12s}: {stats.get('_total', 0)} 条")
    print("\n" + "=" * 60)

    # 列出所有用例
    print("\n所有测试用例:")
    for case in loader.get_all_cases():
        case_id = case.get("case_id", "N/A")
        name = case.get("name", "N/A")
        module = case.get("_module", "N/A")
        print(f"  [{case_id}] {name} ({module})")
