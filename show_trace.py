# -*- coding: utf-8 -*-
"""
查看 Playwright Trace Viewer 的便捷脚本

使用方法：
    python show_trace.py                    # 查看最新trace
    python show_trace.py --list           # 列出所有trace
    python show_trace.py trace_name        # 查看指定trace
"""
import subprocess
import sys
from pathlib import Path

# 使用绝对路径
TRACE_DIR = Path("D:/pythonshiyan/webauto/test-results")


def list_traces():
    """列出所有 trace 文件"""
    if not TRACE_DIR.exists():
        print(f"[X] Trace dir not exists: {TRACE_DIR}")
        print("   Run tests first: pytest tests/ui")
        return []

    traces = sorted(TRACE_DIR.glob("*.zip"), key=lambda x: x.stat().st_mtime, reverse=True)

    if not traces:
        print("[ ] No trace files found")
        print("   Run tests to generate: pytest tests/ui")
        return []

    print(f"\nFound {len(traces)} trace file(s):\n")
    for i, t in enumerate(traces[:10], 1):
        size = t.stat().st_size / 1024
        print(f"  {i}. {t.name} ({size:.1f} KB)")

    if len(traces) > 10:
        print(f"\n  ... and {len(traces) - 10} more")

    return traces


def open_trace(trace_name: str = None):
    """打开指定的 trace 文件"""
    if not trace_name:
        traces = list_traces()
        if traces:
            trace_name = traces[0].name
        else:
            return

    trace_path = TRACE_DIR / trace_name
    if not trace_path.exists():
        print(f"[X] Trace file not found: {trace_path}")
        return

    # 使用 playwright show-trace 命令（使用 python -m 方式）
    print(f"\n[*] Opening Trace Viewer: {trace_name}")
    print(f"    Path: {trace_path}\n")
    try:
        # 方式1：使用 python -m playwright（不阻塞，直接返回）
        subprocess.Popen(
            [sys.executable, "-m", "playwright", "show-trace", str(trace_path)],
            creationflags=subprocess.CREATE_NEW_CONSOLE if sys.platform == "win32" else 0
        )
        print("[*] Trace Viewer 已打开（独立窗口）")
    except Exception:
        # 方式2：直接调用 playwright.exe
        playwright_exe = Path("D:/pythonshiyan/webauto/.venv/Scripts/playwright.exe")
        if playwright_exe.exists():
            subprocess.Popen([str(playwright_exe), "show-trace", str(trace_path)])
            print("[*] Trace Viewer 已打开（独立窗口）")
        else:
            print(f"[X] Playwright not found at: {playwright_exe}")


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Playwright Trace Viewer")
    parser.add_argument("--list", "-l", action="store_true", help="List all traces")
    parser.add_argument("trace_name", nargs="?", help="Trace filename")
    args = parser.parse_args()

    if args.list:
        list_traces()
    elif args.trace_name:
        open_trace(args.trace_name)
    else:
        open_trace()
