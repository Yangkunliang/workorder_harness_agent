# 第三方 Skill 集成指南

## 概述

本项目支持集成第三方 Skill（如 UI/UX Designer、Code Review 等），通过工具注册中心进行统一管理。

---

## 集成方式

### 方式一：命令行调用模式（推荐）

通过 Shell 命令调用外部 Skill：

**配置示例（Nacos agent-tool-registry.json）：**
```json
{
  "ui-ux-designer": {
    "tool_id": "ui-ux-designer",
    "name": "UI/UX 设计师",
    "description": "调用第三方 UI/UX 设计工具",
    "type": "shell",
    "command": "trae run /ui-ux-pro-max",
    "args": ["--input", "{{prd_path}}", "--output", "{{output_path}}"],
    "status": "active",
    "timeout": 300000,
    "max_retry": 0,
    "circuit_threshold": 5,
    "metadata": {
      "requires_prd": true,
      "output_format": "markdown"
    }
  }
}
```

### 方式二：HTTP API 调用模式

通过 HTTP 请求调用外部服务：

**配置示例：**
```json
{
  "ui-ux-designer": {
    "tool_id": "ui-ux-designer",
    "name": "UI/UX 设计师",
    "description": "调用外部 UI/UX 设计 API",
    "type": "http",
    "url": "http://localhost:8080/api/design",
    "method": "POST",
    "headers": {
      "Content-Type": "application/json",
      "Authorization": "Bearer {{API_TOKEN}}"
    },
    "status": "active",
    "timeout": 60000,
    "max_retry": 2,
    "circuit_threshold": 5
  }
}
```

---

## UI/UX Designer 集成配置

### 完整配置示例

```json
{
  "ui-ux-designer": {
    "tool_id": "ui-ux-designer",
    "name": "UI/UX 设计师",
    "description": "基于 PRD 文档生成 UI 设计规范和组件代码",
    "type": "shell",
    "command": "trae",
    "args": [
      "run",
      "/ui-ux-pro-max",
      "--prd",
      "{{prd_file}}",
      "--output-dir",
      "docs/ui-design/{{module_name}}",
      "--format",
      "markdown"
    ],
    "status": "active",
    "timeout": 300000,
    "max_retry": 0,
    "circuit_threshold": 5,
    "metadata": {
      "input": {
        "prd_file": {
          "type": "string",
          "required": true,
          "description": "PRD 文档路径"
        },
        "module_name": {
          "type": "string",
          "required": true,
          "description": "模块名称"
        }
      },
      "output": {
        "design_doc": {
          "type": "string",
          "description": "生成的设计规范文档路径"
        },
        "component_code": {
          "type": "string",
          "description": "生成的组件代码路径"
        }
      }
    }
  }
}
```

### 工作流集成

在 `task-planner` 生成的任务中，自动包含 UI 设计任务：

```json
{
  "id": "T-005",
  "title": "生成 UI 设计规范",
  "description": "基于 PRD 生成页面设计规范和组件代码",
  "type": "design",
  "priority": "P2",
  "dependencies": ["T-001"],
  "tags": ["ui", "design"],
  "steps": [
    {
      "title": "调用 UI/UX Designer",
      "detail": "tool_id: ui-ux-designer, params: {prd_file: docs/prd/user/20240115_login_v1.md, module_name: user}"
    },
    {
      "title": "检查设计文档",
      "detail": "验证输出文件 docs/ui-design/user/20240115_login_design_v1.md 是否存在"
    }
  ],
  "acceptance": ["设计规范文档生成成功", "包含色彩方案、组件设计、交互说明"]
}
```

---

## 变量替换说明

| 变量 | 说明 | 示例值 |
|------|------|--------|
| `{{prd_path}}` | PRD 文档路径 | `docs/prd/user/login.md` |
| `{{output_path}}` | 输出目录 | `docs/ui-design/user/` |
| `{{module_name}}` | 模块名称 | `user` |
| `{{feature_name}}` | 功能名称 | `login` |
| `{{timestamp}}` | 当前时间戳 | `20240115` |

---

## 配置步骤

### 第一步：注册工具

在 Nacos 配置中心 `agent-tool-registry.json` 中添加工具配置。

### 第二步：更新工作流

在 `task-planner` 中添加 UI 设计任务模板。

### 第三步：测试调用

```bash
# 测试工具是否可调用
curl -X POST http://localhost:8000/api/chat \
  -H "Content-Type: application/json" \
  -d '{
    "session_id": "test-session",
    "user_id": "admin",
    "message": "帮我设计用户登录页面的 UI"
  }'
```

---

## 常见问题

### Q1: 第三方 Skill 不在当前环境怎么办？

**解决方案**：确保已安装相关 Skill：
```bash
# 检查已安装的 Skill
trae skills list

# 安装 UI/UX Skill（如果未安装）
trae skills install ui-ux-pro-max
```

### Q2: 如何传递参数给第三方 Skill？

**解决方案**：通过 `args` 数组传递参数，支持模板变量替换：
```json
{
  "args": ["--input", "{{prd_path}}", "--output", "docs/ui-design/{{module}}"]
}
```

### Q3: 如何处理返回结果？

**解决方案**：外部 Skill 执行完成后，结果会写入指定的输出目录，`task-executor` 会验证输出文件是否存在。

---

## 版本历史

| 版本 | 日期 | 更新内容 |
|------|------|----------|
| 1.0 | 2026-06-10 | 初始版本 |