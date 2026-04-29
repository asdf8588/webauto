# -*- coding: utf-8 -*-
"""
WebAuto Test Platform - 定时任务调度器

功能：
- APScheduler 集成到 Django
- 支持定时执行测试任务
- 测试完成后发送通知（企业微信/钉钉/飞书）
- 任务状态自动更新
"""
import os
import sys
import json
import logging
import requests
from datetime import datetime
from pathlib import Path

from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from django.conf import settings

logger = logging.getLogger(__name__)


class NotificationService:
    """通知服务 - 支持多种渠道推送测试结果"""

    @staticmethod
    def send_wecom(webhook_url: str, title: str, passed: int, failed: int, 
                   total: int, report_url: str = None):
        """发送企业微信通知"""
        if not webhook_url:
            logger.warning("企业微信 Webhook URL 未配置")
            return False
        
        try:
            pass_rate = round(passed / (total or 1) * 100, 1)
            
            message = {
                "msgtype": "markdown",
                "markdown": {
                    "content": f"""### 🧪 WebAuto 测试报告\n\n**{title}**\n\n"
                                f"> 📊 **总用例数**: `{total}`\n"
                                f"> ✅ **通过**: `{passed}`\n"
                                f"> ❌ **失败**: `{failed}`\n"
                                f"> 📈 **通过率**: `{pass_rate}%`\n\n"
                                f"{f'> [🔗 查看详细报告]({report_url})' if report_url else ''}\n\n"
                                f"*{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*"""
                }
            }

            resp = requests.post(
                webhook_url,
                json=message,
                timeout=10,
                headers={'Content-Type': 'application/json'}
            )
            
            if resp.status_code == 200 and resp.json().get('errcode') == 0:
                logger.info("✅ 企业微信通知发送成功")
                return True
            else:
                logger.error(f"❌ 企业微信通知失败: {resp.text}")
                return False
                
        except Exception as e:
            logger.error(f"❌ 发送企业微信通知异常: {str(e)}")
            return False

    @staticmethod
    def send_dingtalk(webhook_url: str, title: str, passed: int, failed: int, 
                      total: int, report_url: str = None):
        """发送钉钉通知"""
        if not webhook_url:
            logger.warning("钉钉 Webhook URL 未配置")
            return False
        
        try:
            pass_rate = round(passed / (total or 1) * 100, 1)
            
            message = {
                "msgtype": "markdown",
                "markdown": {
                    "title": f"🧪 测试报告 - {title}",
                    "text": f"""### 🧪 WebAuto 测试报告\n\n**{title}**\n\n"
                            f"- 📊 总用例数: `{total}`\n"
                            f"- ✅ 通过: `{passed}`\n"
                            f"- ❌ 失败: `{failed}`\n"
                            f"- 📈 通过率: `{pass_rate}%`\n\n"
                            f"{f'- [查看详细报告]({report_url})' if report_url else ''}"
                }
            }

            resp = requests.post(
                webhook_url,
                json=message,
                timeout=10,
                headers={'Content-Type': 'application/json'}
            )
            
            if resp.json().get('errcode') == 0:
                logger.info("✅ 钉钉通知发送成功")
                return True
            else:
                logger.error(f"❌ 钉钉通知失败: {resp.text}")
                return False
                
        except Exception as e:
            logger.error(f"❌ 发送钉钉通知异常: {str(e)}")
            return False


class TestScheduler:
    """
    测试任务调度器
    
    使用方法:
        scheduler = TestScheduler()
        scheduler.start()  # 启动调度器
        scheduler.add_task(task)  # 添加定时任务
        scheduler.stop()  # 停止调度器
    """

    def __init__(self):
        self.scheduler = BackgroundScheduler(timezone=settings.TIME_ZONE)
        self.notification = NotificationService()

    def start(self):
        """启动调度器"""
        if not self.scheduler.running:
            self.scheduler.start()
            logger.info("✅ 测试任务调度器已启动")

            # 从数据库加载已保存的定时任务
            self._load_scheduled_tasks()

    def stop(self):
        """停止调度器"""
        if self.scheduler.running:
            self.scheduler.shutdown(wait=False)
            logger.info("⏹️ 测试任务调度器已停止")

    def add_task(self, task):
        """
        添加定时任务
        
        Args:
            task: TestTask 实例（需有 cron_expression 字段）
        """
        try:
            trigger = CronTrigger.from_crontab(task.cron_expression)
            
            job_id = str(task.id)
            
            self.scheduler.add_job(
                func=self._execute_scheduled_task,
                trigger=trigger,
                id=job_id,
                name=f"定时测试: {task.name}",
                args=[task.id],
                replace_existing=True,
            )
            
            logger.info(f"⏰ 已添加定时任务 [{task.name}] -> {task.cron_expression}")
            return True
            
        except Exception as e:
            logger.error(f"❌ 添加定时任务失败: {str(e)}")
            return False

    def remove_task(self, task_id):
        """移除定时任务"""
        job_id = str(task_id)
        job = self.scheduler.get_job(job_id)
        
        if job:
            job.remove()
            logger.info(f"🗑️ 已移除定时任务: {job_id}")
            return True
        return False

    def _execute_scheduled_task(self, task_id):
        """执行定时任务的核心逻辑"""
        from apps.tasks.models import TestTask
        from apps.tasks.executor import TestExecutor

        try:
            task = TestTask.objects.get(id=task_id)
            
            logger.info(f"⏰ 开始执行定时任务: {task.name}")
            
            # 更新任务状态
            task.status = 'running'
            task.started_at = datetime.now()
            task.save(update_fields=['status', 'started_at'])
            
            # 执行测试
            executor = TestExecutor(task)
            executor.run()
            
            # 获取结果并发送通知
            summary = task.result_summary or {}
            passed = summary.get('passed', 0)
            failed = summary.get('failed', 0)
            total = summary.get('total', 0)
            
            # 发送通知（从配置或全局设置获取 webhook）
            config = task.config or {}
            wecom_webhook = config.get('wecom_webhook') or settings.NOTIFICATION_CONFIG.get('wecom_webhook')
            dingtalk_webhook = config.get('dingtalk_webhook') or settings.NOTIFICATION_CONFIG.get('dingtalk_webhook')
            
            report_url = getattr(settings, 'PLATFORM_BASE_URL', '') + f'/api/reports/allure/{task_id}/'
            
            if wecom_webhook:
                self.notification.send_wecom(wecom_webhook, task.name, passed, failed, total, report_url)
                
            if dingtalk_webhook:
                self.notification.send_dingtalk(dingtalk_webhook, task.name, passed, failed, total, report_url)
            
            logger.info(f"✅ 定时任务执行完成: {task.name}")
            
        except Exception as e:
            logger.error(f"❌ 定时任务执行异常: {task_id} - {str(e)}")

    def _load_scheduled_tasks(self):
        """从数据库加载所有启用的定时任务"""
        from apps.tasks.models import TestTask
        
        scheduled_tasks = TestTask.objects.filter(is_scheduled=True).exclude(cron_expression='')
        
        count = 0
        for task in scheduled_tasks:
            if self.add_task(task):
                count += 1
                
        if count > 0:
            logger.info(f"📋 已加载 {count} 个定时任务")


# 全局调度器实例（单例）
_scheduler_instance = None


def get_scheduler():
    """获取全局调度器实例"""
    global _scheduler_instance
    
    if _scheduler_instance is None:
        _scheduler_instance = TestScheduler()
    
    return _scheduler_instance


# Django 启动时自动初始化调度器
_scheduler_ready_called = False

def ready():
    """
    Django 应用就绪时调用
    
    注意：Django 的 ready() 可能被多次调用（这是 Django 官方确认的问题）
    使用标志位防止重复初始化
    """
    global _scheduler_ready_called
    
    if _scheduler_ready_called:
        return  # 防止重复调用
    
    _scheduler_ready_called = True
    
    try:
        scheduler = get_scheduler()
        scheduler.start()
    except Exception as e:
        logger.warning(f"调度器初始化失败（可忽略）: {e}")


if __name__ == '__main__':
    # 直接运行测试
    print("Test Scheduler Module Loaded Successfully")
