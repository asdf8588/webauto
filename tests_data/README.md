# 测试用例目录

统一存放所有 YAML 测试用例，测试平台自动扫描导入。

## 目录结构

```
tests_data/
├── user/           # 用户模块
│   ├── register.yaml   # 注册用例 (5条)
│   ├── login.yaml      # 登录用例 (6条)
│   ├── query.yaml      # 查询用例 (4条)
│   ├── update.yaml     # 更新用例 (3条)
│   └── delete.yaml     # 删除用例 (3条)
├── login/          # 登录模块
│   ├── cases.yaml      # 登录用例 (5条)
│   └── logout.yaml    # 登出用例 (2条)
├── e2e/           # 端到端测试
│   └── user_flow.yaml  # 用户流程 (3条)
└── common/        # 公共用例（预留）
```

## 用例规范

每个 YAML 文件包含多个测试用例，格式如下：

```yaml
- case_id: 模块.功能.序号    # 唯一ID，格式：模块.功能.序号
  name: 用例名称             # 可读名称
  description: 描述          # 详细说明
  module: 模块名             # 所属模块
  priority: P0-P3            # 优先级
  tags: [tag1, tag2]        # 标签
  method: GET/POST/PUT/PATCH/DELETE
  url: /api/path
  body: {}                  # 请求体（可选）
  expected:
    status: 200
    type: success            # success/error
  setup:                    # 前置条件（可选）
    - action: add_user
      name: "User_${uuid}"
      email: "test@example.com"
      password: "123456"
  cleanup: true              # 清理（可选）
```

## 占位符

- `${uuid}` - 自动生成唯一ID
- `${SAME:key}` - 引用同一个测试中的相同值

## 标签说明

- `smoke` - 冒烟测试
- `blocker` - 阻塞级别
- `regression` - 回归测试
- `e2e` - 端到端测试
- `validation` - 验证测试

## 总计

| 模块 | 用例数 |
|------|--------|
| user | 21 |
| login | 7 |
| e2e | 3 |
| **总计** | **31** |
