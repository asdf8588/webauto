# -*- coding: utf-8 -*-
"""
测试执行器 - 核心模块
负责：
1. 构建 pytest 命令
2. 执行测试并捕获输出
3. 生成 Allure 报告
4. 计算质量指标
5. 更新任务状态和结果
"""
import os
import sys
import subprocess
import json
import re
from pathlib import Path
from datetime import datetime

from django.conf import settings


class TestExecutor:
    """
    pytest 测试执行器
    
    使用方法:
        task = TestTask.objects.get(id=task_id)
        executor = TestExecutor(task)
        executor.run()
    """
    
    def __init__(self, task):
        self.task = task
        self.process = None
        self.webauto_root = settings.WEBAUTO_ROOT
        self.output_lines = []
        
    def run(self):
        """执行测试的完整流程"""
        try:
            # 1. 更新状态为 running
            self._update_status('running')
            
            # 2. 构建命令
            cmd = self._build_command()
            self.log('INFO', f'执行命令: {" ".join(cmd)}')
            
            # 3. 执行测试
            start_time = datetime.now()
            exit_code = self._execute(cmd)
            end_time = datetime.now()
            duration = (end_time - start_time).total_seconds()
            
            self.log('INFO', f'执行完成，耗时: {duration:.1f}s')
            
            # 4. 生成 Allure 报告
            self._generate_allure_report()
            
            # 5. 解析结果
            summary = self._parse_results()
            summary['duration'] = round(duration, 1)
            
            # 6. 更新任务状态
            if exit_code == 0:
                self._update_status('completed', result_summary=summary)
                self.log('INFO', f'✅ 测试通过: {summary.get("passed", 0)}/{summary.get("total", 0)}')
            else:
                self._update_status('failed', result_summary=summary)
                self.log('ERROR', f'❌ 测试失败: {summary.get("failed", 0)}/{summary.get("total", 0)}')
                
        except Exception as e:
            self.log('ERROR', f'执行异常: {str(e)}')
            self._update_status('failed')
    
    def _update_status(self, status, result_summary=None):
        """更新任务状态"""
        from .models import TestTask
        
        update_fields = ['status', 'updated_at']
        
        if status == 'running':
            self.task.status = 'running'
            self.task.started_at = datetime.now()
            update_fields.extend(['started_at'])
        elif status in ('completed', 'failed', 'cancelled'):
            self.task.status = status
            self.task.completed_at = datetime.now()
            update_fields.extend(['completed_at'])
        else:
            self.task.status = status
            
        if result_summary:
            self.task.result_summary = result_summary
            update_fields.append('result_summary')
            
        self.task.save(update_fields=update_fields)
    
    def _log(self, level, message):
        """记录日志"""
        from .models import TaskLog
        TaskLog.objects.create(task=self.task, level=level, message=message)
        print(f"[{level}] {message}")
    
    def _build_command(self):
        """构建 pytest 命令"""
        config = self.task.config or {}
        
        # 基础命令
        cmd = [
            sys.executable, '-m', 'pytest',
            '-v',
            '--alluredir=' + str(settings.WEBAUTO_ALLURE_RESULTS),
            '--clean-alluredir',
        ]
        
        # 添加用例路径
        test_ids = config.get('test_ids', [])
        if test_ids:
            from apps.cases.models import TestCase
            cases = TestCase.objects.filter(id__in=test_ids, status='active')
            for case in cases:
                cmd.append(str(self.webauto_root / case.file_path + '::' + case.test_id))
        else:
            # 默认执行所有测试
            cmd.append(str(settings.WEBAUTO_TESTS_DIR))
        
        # 并行执行
        if config.get('parallel') and config.get('workers'):
            cmd.extend(['-n', str(config.get('workers'))])
        
        # 标记过滤
        marker = config.get('marker') or self.task.marker or ''
        if marker:
            cmd.extend(['-m', marker])
        
        # 额外参数
        extra_args = config.get('extra_args', [])
        cmd.extend(extra_args)
        
        return cmd
    
    def _execute(self, cmd):
        """执行命令并实时捕获输出"""
        env = os.environ.copy()
        env['PYTHONPATH'] = str(self.webauto_root)
        
        # 启动子进程
        self.process = subprocess.Popen(
            cmd,
            cwd=str(self.webauto_root),
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1,
            universal_newlines=True,
            env=env,
            creationflags=subprocess.CREATE_NEW_CONSOLE if sys.platform == 'win32' else 0,
        )
        
        # 记录 PID
        self.task.pid = self.process.pid
        self.task.save(update_fields=['pid'])
        
        # 实时读取输出
        for line in iter(self.process.stdout.readline, ''):
            if line:
                line = line.rstrip()
                self.output_lines.append(line)
                
                # 判断日志级别
                if 'PASSED' in line or 'passed' in line.lower():
                    level = 'INFO'
                elif 'FAILED' in line or 'failed' in line.lower() or 'ERROR' in line:
                    level = 'ERROR'
                elif 'WARNING' in line or 'warning' in line.lower():
                    level = 'WARNING'
                else:
                    level = 'DEBUG'
                
                self._log(level, line)
        
        self.process.wait()
        return self.process.returncode
    
    def _generate_allure_report(self):
        """生成 Allure HTML 报告"""
        try:
            report_dir = settings.WEBAUTO_ALLURE_REPORT
            results_dir = settings.WEBAUTO_ALLURE_RESULTS
            
            # 清理旧报告
            if report_dir.exists():
                import shutil
                shutil.rmtree(report_dir)
            
            # 生成新报告
            result = subprocess.run(
                ['allure', 'generate', str(results_dir), '-o', str(report_dir), '--clean'],
                capture_output=True,
                text=True,
                cwd=str(self.webauto_root),
            )
            
            if result.returncode == 0:
                self.task.allure_report_path = str(report_dir)
                self.task.save(update_fields=['allure_report_path'])
                self.log('INFO', '✅ Allure 报告已生成')
                
                # 收集 Trace 文件
                trace_dir = settings.WEBAUTO_TRACE_DIR
                if trace_dir.exists():
                    traces = list(trace_dir.glob("*.zip"))
                    self.task.trace_files = [str(t.name) for t in traces]
                    self.task.save(update_fields=['trace_files'])
            else:
                self.log('WARNING', f'Allure 报告生成失败: {result.stderr}')
                
        except Exception as e:
            self.log('ERROR', f'生成报告异常: {str(e)}')
    
    def _parse_results(self):
        """从 allure-results 解析测试结果"""
        results_dir = settings.WEBAUTO_ALLURE_RESULTS
        summary = {
            'total': 0,
            'passed': 0,
            'failed': 0,
            'broken': 0,
            'skipped': 0,
        }
        
        try:
            for f in Path(results_dir).glob("*-result.json"):
                data = json.loads(f.read_text(encoding='utf-8'))
                s = data.get('status', '')
                summary['total'] += 1
                
                if s == 'passed':
                    summary['passed'] += 1
                elif s == 'failed':
                    summary['failed'] += 1
                elif s == 'broken':
                    summary['broken'] += 1
                elif s == 'skipped':
                    summary['skipped'] += 1
                    
            # 计算通过率
            total = summary['total']
            passed = summary['passed']
            summary['pass_rate'] = round(passed / total * 100, 1) if total > 0 else 0
            
        except Exception as e:
            self.log('ERROR', f'解析结果失败: {str(e)}')
        
        return summary
