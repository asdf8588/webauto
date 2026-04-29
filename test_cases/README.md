# 测试用例目录结构

统一存放所有 YAML 测试用例，支持自动扫描导入。

## 目录结构

```
test_cases/
├── login.yaml              # 登录测试用例 (10条)
├── logout.yaml             # 登出测试用例 (2条)
├── register.yaml           # 注册测试用例 (5条)
├── query.yaml              # 查询测试用例 (3条)
├── update.yaml             # 更新测试用例 (4条)
├── delete.yaml             # 删除测试用例 (3条)
└── e2e.yaml                # 端到端测试用例 (3条)
```

## 用例规范

每个 YAML 文件包含多个测试用例，格式如下：

```yaml
- case_id: TC001                    # 唯一ID
  name: 用例名称                     # 可读名称
  description: 描述                  # 详细说明
  module: 登录模块                    # 所属模块
  priority: P0                       # 优先级 P0-P3
  tags: [smoke, regression]        # 标签
  method: POST                       # 请求方法
  url: /users/login                 # 请求路径
  body:                             # 请求体
    email: "test@example.com"
    password: "123456"
  expected:
    status: 200                     # 期望状态码
    type: success                   # 期望类型: success/error
    message: "登录成功"               # 期望消息（可选）
  setup:                            # 前置条件（可选）
    - action: register
      email: "${AUTO_EMAIL}"
      password: "Test@123456"
  cleanup: true                     # 是否清理（可选）
```

## 占位符

- `${AUTO_UUID}` - 自动生成唯一ID
- `${AUTO_EMAIL}` - 自动生成唯一邮箱
- `${SAME:key}` - 引用同一用例中的相同值

## 标签说明

- `smoke` - 冒烟测试
- `blocker` - 阻塞级别
- `regression` - 回归测试
- `e2e` - 端到端测试
- `validation` - 验证测试

## 总计

| 模块 | 用例数 |
|------|--------|
| login | 10 |
| logout | 2 |
| register | 5 |
| query | 3 |
| update | 4 |
| delete | 3 |
| e2e | 3 |
| **总计** | **30** |
