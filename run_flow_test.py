#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""运行一站式闭环测试"""
import subprocess
import sys

result = subprocess.run(
    [sys.executable, "-m", "pytest", 
     "tests/api/test_integration_flow.py", 
     "-v", "--tb=short"],
    capture_output=True,
    text=False  # 使用二进制输出避免编码问题
)

# 尝试不同编码
for enc in ['utf-8', 'gbk', 'latin-1']:
    try:
        stdout = result.stdout.decode(enc)
        stderr = result.stderr.decode(enc)
        break
    except:
        continue

print(stdout)
if stderr:
    print("STDERR:", stderr)
print(f"\nExit code: {result.returncode}")
