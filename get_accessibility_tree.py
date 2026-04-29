# -*- coding: utf-8 -*-
"""
无障碍树生成工具 - 根据页面 aria_snapshot 生成 JSON 文件

使用方法：
    python get_accessibility_tree.py                    # 生成所有页面
    python get_accessibility_tree.py --url /login.html  # 生成指定页面
    python get_accessibility_tree.py --list             # 列出可用页面
"""
import os
import re
import json
import argparse
import sys
from pathlib import Path

# Windows 控制台编码修复
if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

from playwright.sync_api import sync_playwright

BASE_URL = os.getenv("BASE_URL", "http://localhost:8080")
A11Y_DIR = Path(__file__).parent / "a11y"

# 所有需要生成无障碍树的页面
PAGES = {
    "index": "/index.html",
    "login": "/login.html",
    "users": "/users.html",
    "add_user": "/addUser.html",
    "user_info": "/userInfo.html",
    "update_password": "/updatePassword.html",
    "update_user": "/updateUser.html",
}


def generate_snapshot(url: str, output_file: str) -> dict:
    """生成单个页面的无障碍树快照"""
    full_url = f"{BASE_URL}{url}" if url.startswith("/") else url
    
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        page.goto(full_url, wait_until="networkidle")
        
        # 获取 aria_snapshot
        snapshot = page.locator("body").aria_snapshot()
        
        # 解析快照为结构化数据
        elements = _parse_snapshot(snapshot)
        
        browser.close()
        
        # 保存原始快照
        output_path = A11Y_DIR / output_file
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(snapshot)
        
        # 保存解析后的 JSON
        json_path = A11Y_DIR / output_file.replace(".json", "_parsed.json")
        with open(json_path, "w", encoding="utf-8") as f:
            json.dump(elements, f, ensure_ascii=False, indent=2)
        
        print(f"✓ {output_file} ({len(elements)} 元素)")
        return elements


def _parse_snapshot(snapshot: str) -> list:
    """解析 aria_snapshot 文本为结构化列表"""
    elements = []
    lines = snapshot.split("\n")
    
    for line in lines:
        line = line.strip()
        if not line:
            continue
        
        # 匹配行: - role "name" [attributes]
        # 例如: - heading "标题" [level=1]
        #       - textbox: value
        match = re.match(r"^- (\w+)(?:\s+\"([^\"]+)\")?(?:\s*:\s*(.*))?(?:\[(.*)\])?$", line)
        
        if match:
            role = match.group(1)
            name = match.group(2) or ""
            value = match.group(3) or ""
            attrs_str = match.group(4) or ""
            
            # 解析属性
            attrs = {}
            if attrs_str:
                for attr in attrs_str.split(","):
                    if "=" in attr:
                        k, v = attr.split("=", 1)
                        attrs[k.strip()] = v.strip()
            
            # 提取 URL (如果有)
            url = None
            if "/url:" in value:
                url_match = re.search(r"/url:\s*(/\S+)", value)
                if url_match:
                    url = url_match.group(1)
                value = re.sub(r"\s*/url:\s*/\S+", "", value).strip()
            
            elem = {
                "role": role,
                "name": name.strip(),
                "value": value.strip() if value else "",
                "attrs": attrs,
                "url": url,
            }
            
            # 生成推荐定位器
            elem["locators"] = _generate_locators(role, name, value, attrs)
            
            elements.append(elem)
    
    return elements


def _generate_locators(role: str, name: str, value: str, attrs: dict) -> list:
    """根据元素信息生成推荐的 Playwright 定位器"""
    locators = []
    
    # 1. get_by_role + 正则 (推荐)
    if name:
        # 精确匹配
        locators.append({
            "type": "get_by_role",
            "code": f'get_by_role("{role}", name=re.compile(r"{re.escape(name)}"))',
            "description": f"按角色'{role}' + 名称包含'{name}'"
        })
        
        # 模糊匹配 (更灵活)
        keywords = name.split()
        if keywords:
            pattern = ".*".join(re.escape(k) for k in keywords if len(k) > 1)
            locators.append({
                "type": "get_by_role_regex",
                "code": f'get_by_role("{role}", name=re.compile(r".*{pattern}.*"))',
                "description": f"按角色'{role}' + 模糊匹配"
            })
    
    # 2. get_by_label (表单元素)
    if role == "textbox" and name:
        locators.append({
            "type": "get_by_label",
            "code": f'get_by_label(re.compile(r"{re.escape(name)}"))',
            "description": "按标签文本"
        })
    
    # 3. get_by_placeholder
    if "placeholder" in attrs:
        locators.append({
            "type": "get_by_placeholder",
            "code": f'get_by_placeholder(re.compile(r"{re.escape(attrs["placeholder"])}"))',
            "description": "按占位符"
        })
    
    # 4. get_by_title
    if "title" in attrs:
        locators.append({
            "type": "get_by_title",
            "code": f'get_by_title(re.compile(r"{re.escape(attrs["title"])}"))',
            "description": "按标题"
        })
    
    return locators


def list_pages():
    """列出所有可用页面"""
    print("可用页面:")
    for name, path in PAGES.items():
        print(f"  {name:15} {path}")


def main():
    parser = argparse.ArgumentParser(description="无障碍树生成工具")
    parser.add_argument("--url", "-u", help="指定页面路径，如 /login.html")
    parser.add_argument("--list", "-l", action="store_true", help="列出所有可用页面")
    parser.add_argument("--name", "-n", help="指定输出文件名(不含扩展名)")
    args = parser.parse_args()
    
    if args.list:
        list_pages()
        return
    
    # 确保输出目录存在
    A11Y_DIR.mkdir(exist_ok=True)
    
    if args.url:
        # 生成指定页面
        filename = args.name or args.url.strip("/").replace("/", "_") + ".json"
        generate_snapshot(args.url, filename)
    else:
        # 生成所有页面
        print(f"目标服务器: {BASE_URL}")
        print(f"输出目录: {A11Y_DIR}\n")
        
        for name, path in PAGES.items():
            generate_snapshot(path, f"a11y_{name}.json")


if __name__ == "__main__":
    main()
