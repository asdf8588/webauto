# WebAuto Test Platform

> 基于 **Django + Vue 3 + pytest + Allure + Playwright** 的企业级自动化测试平台

## 功能特性

| 模块 | 功能 | 说明 |
|------|------|------|
| 🧪 用例管理 | CRUD、自动扫描导入 | 从 `webauto/tests/` 自动发现所有测试用例 |
| ▶️ 任务执行 | 单个/批量/套件执行 | 支持并行、标记过滤、实时日志 |
| 📊 报告查看 | Allure 报告嵌入 | iframe 嵌入，支持历史报告切换 |
| 🎬 Trace 查看 | Playwright Trace | 列表展示、在线预览、下载 |
| ⏰ 定时任务 | Cron 定时执行 | APScheduler 集成 |
| 🔔 通知推送 | 企业微信/钉钉/飞书 | Webhook 推送测试结果 |

## 快速开始

### 1. 安装依赖

```bash
# 后端
cd platform/backend
pip install -r requirements.txt
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt

# 前端
cd ../frontend
npm install
```

### 2. 初始化数据库

```bash
cd platform/backend
python manage.py makemigrations
python manage.py migrate
python manage.py createsuperuser  # 创建管理员账号
```

### 3. 启动服务

**方式一：分别启动（开发推荐）**

```bash
# 终端1: 启动后端 (端口 8000)
cd platform/backend
python manage.py runserver 0.0.0.0:8000

# 终端2: 启动前端 (端口 5173)
cd platform/frontend
npm run dev
```

**访问地址**: http://localhost:5173

### 4. 扫描用例

在平台的「用例管理」页面点击「扫描导入」，或调用 API：

```bash
curl -X POST http://localhost:8000/api/cases/testcases/scan/
```

## 项目结构

```
platform/
├── backend/                    # Django 后端
│   ├── test_platform/          # Django 项目配置
│   │   ├── settings.py         # 全局配置（路径、数据库等）
│   │   ├── urls.py             # 路由配置
│   │   └── wsgi.py / asgi.py
│   ├── apps/
│   │   ├── cases/              # 用例管理模块
│   │   │   ├── models.py        # TestCase, TestSuite 模型
│   │   │   ├── views.py         # REST API Views
│   │   │   └── executor.py      # 测试执行器
│   │   ├── tasks/              # 任务执行模块
│   │   │   ├── models.py        # TestTask, TaskLog 模型
│   │   │   ├── executor.py      # pytest 执行引擎
│   │   │   └── scheduler.py     # APScheduler 定时任务
│   │   └── reports/            # 报告模块
│   │       ├── views.py         # Allure 报告代理
│   │       └── models.py        # 报告记录模型
│   ├── templates/
│   │   └── allure_proxy.html   # Allure 报告代理页
│   ├── scheduler.py            # 定时任务调度器入口
│   ├── manage.py               # Django 管理命令
│   └── requirements.txt
│
├── frontend/                   # Vue 3 前端
│   ├── src/
│   │   ├── views/             # 页面组件
│   │   │   ├── Dashboard.vue   # 工作台（仪表盘）
│   │   │   ├── Cases.vue       # 用例管理
│   │   │   ├── Tasks.vue       # 执行任务
│   │   │   ├── Reports.vue     # 测试报告
│   │   │   ├── Traces.vue      # Trace 查看
│   │   │   └── Settings.vue    # 设置页面
│   │   ├── components/
│   │   │   └── TaskLogViewer.vue  # 实时日志组件
│   │   ├── router/index.js     # 路由配置
│   │   ├── App.vue             # 根组件（导航栏）
│   │   └── main.js             # 入口文件
│   ├── vite.config.js          # Vite 配置（含代理）
│   └── package.json
```

## 核心技术栈

| 层级 | 技术 | 版本 |
|------|------|------|
| 后端框架 | Django + DRF | 4.2+ / 3.14+ |
| 前端框架 | Vue 3 + Element Plus | 3.4+ / 2.9+ |
| 构建工具 | Vite | 6.0+ |
| 测试执行 | pytest + playwright | - |
| 测试报告 | Allure | 2.x |
| 定时任务 | APScheduler | 3.10+ |
| 数据库 | SQLite (开发) / MySQL (生产) | - |

## API 接口

### 用例管理

```
GET    /api/cases/testcases/       # 获取用例列表
POST   /api/cases/testcases/scan/  # 扫描导入用例
GET    /api/cases/testcases/stats/ # 获取统计信息
PUT    /api/cases/testcases/{id}/  # 更新用例
POST   /api/cases/testcases/{id}/toggle/  # 切换启用状态
```

### 任务执行

```
GET    /api/tasks/running/         # 运行中的任务
POST   /api/tasks/run_quick/       # 快速创建并执行
POST   /api/tasks/{id}/execute/    # 执行指定任务
POST   /api/tasks/{id}/stop/       # 停止任务
GET    /api/tasks/{id}/logs/       # 获取任务日志
GET    /api/tasks/history/         # 执行历史
```

### 报告查看

```
GET    /api/reports/list-reports/  # 报告列表
GET    /api/reports/latest/        # 最新报告信息
GET    /api/reports/dashboard/     # 仪表盘统计数据
GET    /api/reports/traces/        # Trace 文件列表
GET    /allure/                    # Allure 报告页面
GET    /allure-data/               # 报告数据文件代理
```

## 定时任务与通知

### 配置定时任务

1. 在「设置」页面配置 Webhook
2. 创建任务时勾选「定时任务」并设置 Cron 表达式
3. 示例 Cron：
   ```
   每天 9:00:  0 9 * * *
   每2小时:    0 */2 * * *
   工作日 18:00: 0 18 * * 1-5
   ```

### 企业微信通知配置

1. 在企业微信群添加机器人
2. 复制 Webhook URL
3. 填入设置页面的「企业微信 Webhook」

## 开发指南

### 添加新的用例类型

1. 在 `apps/cases/models.py` 的 `TYPE_CHOICES` 中添加新类型
2. 更新 `TestCase.scan_from_directory()` 的判断逻辑
3. 前端 `Cases.vue` 的过滤器会自动识别

### 自定义报告模板

编辑 `templates/allure_proxy.html` 可以自定义报告嵌入样式。

### 扩展通知渠道

在 `scheduler.py` 的 `NotificationService` 类中添加新方法即可。

## 参考资源

- [Django REST Framework 官方文档](https://www.django-rest-framework.org/)
- [Vue 3 官方文档](https://cn.vuejs.org/)
- [Element Plus 组件库](https://element-plus.org/)
- [Allure 报告官方文档](https://allurereport.org/docs/pytest/)
- [Playwright Python 文档](https://playwright.dev/python/)
- [APScheduler 文档](https://apscheduler.readthedocs.io/)

## License

MIT
