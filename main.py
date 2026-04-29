# -*- coding: utf-8 -*-
"""
一键执行所有测试 + Allure 报告 + 质量指标 + 并行测试支持
"""
import os
import sys
import pytest
import json
import argparse
from pathlib import Path

# 将项目根目录添加到 sys.path，确保能正确导入模块
ROOT_DIR = os.path.dirname(os.path.abspath(__file__))
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

# 质量指标计算
def calc_quality_metrics(results_dir):
    """从 allure-results 计算质量指标"""
    total = passed = failed = broken = skipped = expected = 0

    for f in Path(results_dir).glob("*-result.json"):
        try:
            data = json.loads(f.read_text(encoding="utf-8"))
            s = data.get("status", "")
            if s == "passed":
                passed += 1
            elif s == "failed":
                failed += 1
            elif s == "broken":
                broken += 1
            elif s == "skipped":
                skipped += 1
            elif s == "expected-failure":
                expected += 1
            total += 1
        except:
            pass

    # 计算指标
    # 功能通过率 = Passed / (Total - Skipped - Expected_Failure)
    functional = (passed / (total - skipped - expected) * 100) if (total - skipped - expected) > 0 else 0

    # 缺陷检出率 = Failed / (Total - Skipped)
    defect = (failed / (total - skipped) * 100) if (total - skipped) > 0 else 0

    # 测试通过率 = (Passed + Expected) / (Total - Skipped)
    test_pass = ((passed + expected) / (total - skipped) * 100) if (total - skipped) > 0 else 0

    # 测试稳定性 = Passed / (Passed + Failed + Broken)
    stability = (passed / (passed + failed + broken) * 100) if (passed + failed + broken) > 0 else 0

    return {
        "total": total, "passed": passed, "failed": failed,
        "broken": broken, "skipped": skipped, "expected": expected,
        "functional": round(functional, 1),
        "defect": round(defect, 1),
        "test_pass": round(test_pass, 1),
        "stability": round(stability, 1),
    }

# 注入指标到报告
def inject_metrics(metrics):
    """注入质量指标到 allure 报告"""
    report_dir = Path("allure-report")
    summary = report_dir / "widgets" / "summary.json"

    if summary.exists():
        data = json.loads(summary.read_text(encoding="utf-8"))
        data["qualityMetrics"] = {
            "functionalRate": metrics["functional"],
            "defectRate": metrics["defect"],
            "testPassRate": metrics["test_pass"],
            "stability": metrics["stability"],
        }
        summary.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")

    # 注入到 index.html
    index = report_dir / "index.html"
    if index.exists():
        m = metrics
        html = f'''
<div class="metrics-grid">
    <div class="metric green">
        <div class="label">功能通过率</div>
        <div class="value">{m['functional']}%</div>
    </div>
    <div class="metric red">
        <div class="label">缺陷检出率</div>
        <div class="value">{m['defect']}%</div>
    </div>
    <div class="metric blue">
        <div class="label">测试通过率</div>
        <div class="value">{m['test_pass']}%</div>
    </div>
    <div class="metric yellow">
        <div class="label">测试稳定性</div>
        <div class="value">{m['stability']}%</div>
    </div>
</div>
<style>
.metrics-grid{{display:flex;gap:12px;padding:16px;background:#1a1f2e}}
.metric{{background:#132035;border-radius:8px;padding:16px;flex:1;text-align:center}}
.metric.green{{border-left:3px solid #4ade80}}
.metric.red{{border-left:3px solid #f87171}}
.metric.blue{{border-left:3px solid #60a5fa}}
.metric.yellow{{border-left:3px solid #fbbf24}}
.label{{color:#64748b;font-size:11px}}
.value{{color:#fff;font-size:24px;font-weight:700;margin-top:4px}}
</style>
'''
        content = index.read_text(encoding="utf-8")
        if "metrics-grid" not in content:
            content = content.replace('<div id="content">', f"{html}\n    <div id=\"content\">", 1)
            index.write_text(content, encoding="utf-8")

# ═══════════════════════════════════════════════════════════════════
if __name__ == "__main__":
    # 解析命令行参数
    parser = argparse.ArgumentParser(description="测试执行器")
    parser.add_argument("-n", "--workers", type=str, default=None,
                        help="并行测试进程数，如 -n auto (自动) 或 -n 4 (4个进程)")
    parser.add_argument("-m", "--markers", type=str, default=None,
                        help="只运行指定标记的测试，如 -m smoke")
    args = parser.parse_args()

    # 构建 pytest 参数
    pytest_args = ["-v", "--alluredir=./allure-results", "--clean-alluredir"]

    # 添加并行测试（-n 和值必须分开传递，pytest.main() 会分别解析每个元素）
    if args.workers:
        pytest_args.extend(["-n", args.workers])
        print(f"[并行模式] 启动 {args.workers} 个工作进程")

    # 添加标记过滤（-m 和值必须分开传递）
    if args.markers:
        pytest_args.extend(["-m", args.markers])
        print(f"[标记过滤] 只运行 {args.markers} 测试")

    # 1. 执行所有测试
    print("\n" + "="*60)
    print("开始执行测试...")
    print("="*60 + "\n")
    pytest.main(pytest_args)

    # 2. 生成报告
    os.system("allure generate ./allure-results -o ./allure-report --clean")

    # 3. 计算并注入质量指标
    metrics = calc_quality_metrics("allure-results")
    inject_metrics(metrics)

    # 4. 打印指标
    print(f"""
╔══════════════════════════════════════════════════════════╗
║                    质量指标报告                            ║
╠══════════════════════════════════════════════════════════╣
║  总用例数: {metrics['total']:<6}  通过: {metrics['passed']:<4}  失败: {metrics['failed']:<4}  ║
╠══════════════════════════════════════════════════════════╣
║  功能通过率: {metrics['functional']}%   (软件满足核心需求)        ║
║  缺陷检出率: {metrics['defect']}%   (测试发现 Bug 能力)          ║
║  测试通过率: {metrics['test_pass']}%   (用例健康度)              ║
║  测试稳定性: {metrics['stability']}%   (用例健壮性)              ║
╚══════════════════════════════════════════════════════════╝
""")
