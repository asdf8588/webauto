# OpenAPI 集成示例

本项目演示了如何将 OpenAPI 规范与测试项目集成。

## 文件结构

```
webauto/
├── api_specs/
│   └── openapi.yaml          # OpenAPI 规范文件（定义 API 接口）
├── openapi_validator.py      # 验证和测试生成工具
├── tests/
│   └── api/
│       └── test_generated_from_openapi.py  # 自动生成的测试
└── README_OPENAPI.md         # 本文档
```

## 什么是 OpenAPI？

OpenAPI 规范（以前叫 Swagger）是一种用 YAML/JSON 描述 REST API 的标准格式。

简单来说：
- **传统方式**：手动写测试用例
- **OpenAPI 方式**：先定义 API 规范，再自动生成测试

## 快速开始

### 1. 查看 OpenAPI 规范

```bash
python openapi_validator.py
```

会显示规范的摘要信息：
- API 路径和 HTTP 方法
- 请求参数和响应格式
- 数据模型（Schema）

### 2. 验证规范文件

```bash
python openapi_validator.py --validate
```

这会检查：
- 规范文件语法是否正确
- Schema 定义是否完整
- API 路径定义是否规范

### 3. 生成测试代码

```bash
python openapi_validator.py --generate
```

根据 OpenAPI 规范自动生成 pytest 测试代码。

### 4. 启动 Mock 服务器

```bash
python openapi_validator.py --serve
```

启动一个模拟 API 服务器，返回符合规范定义的响应。用于测试。

### 5. 运行生成的测试

```bash
pytest tests/api/test_generated_from_openapi.py -v
```

## OpenAPI 规范示例

OpenAPI 规范文件 (`api_specs/openapi.yaml`) 包含以下部分：

```yaml
openapi: 3.0.3           # 版本号
info:                    # API 描述
  title: 用户认证系统 API
  version: 1.0.0

paths:                   # API 路径
  /users/login:
    post:
      summary: 用户登录
      requestBody:
        content:
          application/json:
            schema:
              type: object
              properties:
                email:
                  type: string
                  format: email
                password:
                  type: string
      responses:
        '200':
          description: 登录成功
          content:
            application/json:
              schema:
                type: object
                properties:
                  status:
                    type: integer
                  type:
                    type: string
                  message:
                    type: string
```

## OpenAPI 规范格式说明

### 1. 顶级字段

| 字段 | 说明 | 必填 |
|-----|------|-----|
| `openapi` | OpenAPI 版本号，如 "3.0.3" | 是 |
| `info` | API 元信息（标题、版本、描述） | 是 |
| `paths` | API 路径定义 | 是 |
| `components` | 可复用组件（Schema、安全方案） | 否 |

### 2. 请求体定义

```yaml
requestBody:
  required: true                    # 是否必填
  content:
    application/json:                # Content-Type
      schema:                        # 数据结构
        type: object
        properties:
          name:
            type: string
            description: 用户名
          email:
            type: string
            format: email
        required:                   # 必填字段
          - email
          - password
```

### 3. 响应定义

```yaml
responses:
  '200':
    description: 成功响应
    content:
      application/json:
        schema:
          type: object
          properties:
            status:
              type: integer
              example: 200
            message:
              type: string
              example: "操作成功"
```

### 4. Schema 复用

在 `components/schemas` 定义的数据模型可以在多处引用：

```yaml
components:
  schemas:
    User:
      type: object
      properties:
        id:
          type: integer
        name:
          type: string

# 引用方式：
schemas:
  $ref: '#/components/schemas/User'
```

## 工具功能

### openapi_validator.py

| 功能 | 命令 | 说明 |
|-----|------|-----|
| 验证规范 | `--validate` | 检查语法和结构 |
| 启动 Mock | `--serve` | 模拟 API 服务器 |
| 生成测试 | `--generate` | 生成 pytest 代码 |
| 指定文件 | `--spec path/to/file.yaml` | 指定规范文件 |
| 指定端口 | `--port 9000` | Mock 服务器端口 |

### 常用命令

```bash
# 1. 验证规范是否正确
python openapi_validator.py --validate

# 2. 生成测试代码
python openapi_validator.py --generate

# 3. 启动 Mock 服务器（新开终端）
python openapi_validator.py --serve

# 4. 运行测试（需要先启动 Mock）
pytest tests/api/test_generated_from_openapi.py -v
```

## 学习要点

1. **规范优先**：先定义接口规范，再写代码
2. **契约测试**：API 必须符合规范定义
3. **代码生成**：减少重复的测试代码
4. **文档即测试**：规范文件既是文档也是测试

## 进阶用法

### 1. 使用 Swagger Editor 编辑规范

访问 https://editor.swagger.io/ ，粘贴 `api_specs/openapi.yaml` 的内容，可以可视化编辑和预览。

### 2. 使用 Apifox 管理规范

Apifox 是一个 API 管理工具，支持：
- OpenAPI 导入/导出
- Mock 服务器
- 接口文档
- 自动生成测试用例

### 3. 第三方工具

| 工具 | 用途 |
|-----|-----|
| `openapi-spec-validator` | Python 规范验证 |
| `prance` | OpenAPI 解析和处理 |
| `swagger-codegen` | 生成客户端代码 |
| `redocly` | 生成 API 文档 |
| `Dredd` | API 契约测试 |

## 与现有测试的关系

| 现有测试 | OpenAPI 方式 |
|---------|-------------|
| `test_cases/*.yaml` 手动用例 | 自动从规范生成 |
| `tests/api/` 测试代码 | 可以部分自动生成 |
| 变量替换 `${AUTO_UUID}` | 需要额外处理 |

## 注意事项

1. 自动生成的测试只是基础模板，复杂逻辑需要手动补充
2. Mock 服务器是简化实现，仅用于演示
3. 建议将 OpenAPI 规范文件纳入版本控制
4. 规范变更时要记得重新生成测试代码

## 参考资料

- [OpenAPI 规范文档](https://spec.openapis.org/oas/latest.html)
- [Swagger Editor](https://editor.swagger.io/)
- [OpenAPI Validator](https://github.com/p1c2u/openapi-spec-validator)
