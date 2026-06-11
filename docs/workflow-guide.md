# 软件开发工作流系统

## 概述

本项目实现了一个完整的企业级软件开发工作流系统，支持从需求分析到代码实现的全流程管理。

---

## 工作流架构

```
指挥官 → 产品经理 → UI/UX设计师 → 技术设计师 → 任务规划师 → 任务执行者 → 单元测试 → Bug修复(循环) → E2E测试 → 部署
              ↓           ↓            ↓            ↓             ↓            ↓         ↓(循环)        ↓         ↓
         docs/prd/   docs/ui-design/  docs/tech/   docs/tasks/    src/       tests/     fix/        e2e/     github
```

### 状态机流程图

```
┌─────────┐     prd_valid      ┌─────────┐   design_valid   ┌─────────┐
│   PRD   │ ─────────────────> │   UI    │ ───────────────> │  Tech   │
└─────────┘                   │ Design  │                  │ Design  │
                              └─────────┘                  └─────────┘
                                     │                            │
                                     ▼                            ▼
                            ┌─────────┐                  ┌─────────┐
                            │  Tasks  │ ── tasks_valid ──> │Execute  │
                            └─────────┘                  └─────────┘
                                                                      │
                    ┌────────────────────────────────────────────────┘
                    │
                    ▼
            ┌───────────────┐
            │   单元测试     │
            │               │
            │  ┌─────────┐  │
            │  │测试通过? │  │
            │  └────┬────┘  │
            │       │       │
            │  通过  │  失败 │
            │       ▼       ▼
            │   [E2E]   [Bug修复]
            │   测试    ─────────┐
            │       │           │
            │       ▼           ▼
            │   ┌─────────┐ 重新测试
            │   │E2E通过? │
            │   └────┬────┘
            │        │
            │   通过 │ 失败
            │        ▼
            │   [Deploy]  [Bug修复]
            │      │          │
            │      ▼          ▼
            │   [完成]    重新测试
            └───────────────┘
```

### 测试-修复循环机制

工作流支持自动化测试-修复-重新测试循环：

| 参数 | 值 | 说明 |
|------|-----|------|
| max_retry_count | 5 | 最大自动重试次数 |
| retry_delay_seconds | 5 | 重试间隔（秒） |
| test_pass_threshold | 100 | 测试通过阈值（%） |

---

## Skill 列表

| Skill | 名称 | 职责 | 执行方式 | 输出产物 |
|-------|------|------|----------|----------|
| product-manager | 产品经理 | 需求分析、PRD 撰写 | 内置模板 | `docs/prd/xxx.md` |
| ui-designer | UI/UX 设计师 | 界面设计规范 | **外部调用 ui-ux-pro-max** | `docs/ui-design/xxx.md` |
| tech-designer | 技术设计师 | 技术方案设计 | 内置模板 | `docs/tech/xxx.md` |
| task-planner | 任务规划师 | 任务拆解 | 内置模板 | `docs/tasks/xxx.json` |
| task-executor | 任务执行者 | 代码实现 | 内置模板 | `src/` |
| code-review | 代码审查师 | 代码分析和自动修复 | **建议外部集成** | 修复后的代码 |
| unit-tester | 单元测试工程师 | 单元测试编写 | 内置模板 | `tests/unit/xxx.py` |
| e2e-runner | E2E 测试执行者 | 端到端测试 | 内置模板 | `docs/tests/xxx.md` |
| github-deploy | GitHub 部署 | 代码部署 | 内置模板 | - |

### Skill 获取建议

| Skill | 来源 | 推荐度 | 说明 |
|-------|------|--------|------|
| product-manager | 内置 | ★★★★★ | 已完成 |
| ui-designer | 外部 ui-ux-pro-max | ★★★★★ | 已集成 |
| tech-designer | 内置 | ★★★★★ | 已完成 |
| task-planner | 内置 | ★★★★★ | 已完成 |
| task-executor | 内置 | ★★★★★ | 已完成 |
| **code-review** | **建议外部** | ★★★★☆ | **待集成** |
| unit-tester | 内置 | ★★★★★ | 已完成 |
| e2e-runner | 内置 | ★★★★☆ | 基础功能 |
| github-deploy | 内置 | ★★★★★ | 已完成 |

**code-review Skill 推荐方案：**

1. **使用外部现成 Skill**
   - 推荐 GitHub 上的 `trae-code-review-skill`
   - 或类似的代码审查工具

2. **自研方案**
   - 基于静态分析工具（flake8, pylint, mypy）
   - 结合 LLM 进行智能代码审查
   - 支持自动修复常见问题

3. **临时方案**
   - 在 hooks 中跳过自动修复，通知人工审查
   - 配置 `max_retry_count: 0` 禁用自动修复

---

## 工作流程详解

### 阶段一：需求分析（产品经理）

1. 分析用户提供的需求材料
2. 扫描已有 PRD 文档，识别关联模块
3. 一次性批量提问，收集完整需求信息
4. 生成验收标准草稿
5. 输出 PRD 文档

### 阶段二：UI/UX 设计（UI/UX 设计师）

1. 读取 PRD 文档，理解功能需求
2. 调用外部 Skill（ui-ux-pro-max）生成设计规范
3. 输出设计文档到 `docs/ui-design/`
4. 更新设计文档索引

### 阶段三：技术设计（技术设计师）

1. 确认项目技术栈
2. 分析 PRD 文档和 UI 设计规范
3. 设计数据模型和 API 接口
4. 制定缓存方案和错误码体系
5. 输出技术设计文档

### 阶段四：任务规划（任务规划师）

1. 读取上游文档（PRD、UI设计、技术设计）
2. 扫描已有代码结构
3. 拆解任务，定义依赖关系
4. 输出 JSON 任务列表

### 阶段五：任务执行（任务执行者）

1. 读取任务 JSON 文件
2. 按依赖顺序执行任务
3. 每步完成后验证
4. 更新进度文件

### 阶段六：自动化测试（测试执行者）

1. 单元测试：生成并执行单元测试用例
2. E2E 测试：生成并执行端到端测试用例
3. 生成测试报告
4. 失败用例自动创建 Bug 工单

---

## 文档目录结构

```
docs/
├── prd/                    # 产品需求文档
│   ├── <模块名>/
│   │   └── <YYYYMMDD>_<功能名>_v<版本号>.md
│   └── README.md           # PRD 索引
├── tech/                   # 技术设计文档
│   ├── <模块名>/
│   │   └── <YYYYMMDD>_<模块名>_v<版本号>.md
│   └── README.md           # 技术文档索引
├── tasks/                  # 任务列表
│   ├── <模块名>/
│   │   └── <YYYYMMDD>_<功能名>_v<版本号>.json
│   └── README.md           # 任务索引
├── ui-design/              # UI 设计稿
│   ├── <模块名>/
│   │   └── <YYYYMMDD>_<页面名>_design_v<版本号>.md
│   └── README.md           # UI 设计索引
├── tests/                  # 测试报告
│   └── <模块名>/
│       └── <YYYYMMDD>_<功能名>_test_report_v<版本号>.md
└── specs/                  # 全局规范
    ├── 全局技术规范.md
    └── 第三方Skill集成指南.md
```

### 文档命名规则

| 组成部分 | 格式 | 说明 |
|----------|------|------|
| `<模块名>` | 小写字母+下划线 | 如 `user`, `order`, `workflow` |
| `<YYYYMMDD>` | 年月日 | 创建日期，便于版本追溯 |
| `<功能名>` | 小写字母+下划线 | 如 `login`, `query_order` |
| `<版本号>` | v1, v2... | 同一功能多次迭代时递增 |

---

## 任务 JSON 格式

```json
{
  "meta": {
    "name": "功能名称",
    "description": "描述",
    "version": "1.0",
    "date": "2026-06-10",
    "author": "Task Planner",
    "status": "draft",
    "references": {
      "prd": ["docs/prd/xxx.md"],
      "tech_design": ["docs/tech/xxx.md"]
    }
  },
  "tasks": [
    {
      "id": "T-001",
      "title": "任务标题",
      "description": "任务描述",
      "type": "feature",
      "priority": "P1",
      "effort": "M",
      "dependencies": [],
      "tags": ["backend"],
      "steps": [
        {"title": "步骤1", "detail": "实现要点"}
      ],
      "acceptance": ["验收标准"],
      "completed": false
    }
  ]
}
```

---

## 使用示例

```bash
# 1. 启动产品经理 Skill，输入需求
trae run /product-manager
# 输出 PRD 文档 → docs/prd/user/20240115_login_v1.md

# 2. 启动 UI/UX 设计师（调用外部 ui-ux-pro-max）
trae run /ui-designer
# 输出设计文档 → docs/ui-design/user/20240115_login_page_design_v1.md

# 3. 启动技术设计师 Skill
trae run /tech-designer
# 输出技术设计文档 → docs/tech/user/20240115_user_service_v1.md

# 4. 启动任务规划师 Skill
trae run /task-planner
# 输出任务列表 → docs/tasks/user/20240115_login_v1.json

# 5. 启动任务执行者 Skill
trae run /task-executor
# 生成代码 → src/api/user.py, src/services/user_service.py

# 6. 启动单元测试工程师
trae run /unit-tester
# 生成单元测试 → tests/unit/test_user_service.py

# 7. 启动 E2E 测试执行者
trae run /e2e-runner
# 生成测试报告 → docs/tests/user/20240115_login_test_report_v1.md

# 8. 部署到 GitHub
trae run /github-deploy
```

---

## 阶段门禁规则

每个阶段需要用户明确确认（如"可以"、"继续"、"没问题"等），才可进入下一阶段：

1. **材料分析完成** → 用户确认 → 进入需求收集
2. **需求收集完成** → 用户确认 → 进入验收标准
3. **验收标准确认** → 用户确认 → 输出 PRD
4. **技术设计完成** → 用户确认 → 输出技术文档
5. **任务拆解完成** → 用户确认 → 输出任务列表
6. **任务执行完成** → 用户确认 → 完成

---

## 版本历史

| 版本 | 日期 | 更新内容 |
|------|------|----------|
| 1.0 | 2026-06-10 | 初始版本 |