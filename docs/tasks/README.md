# 任务列表

## 目录结构

```
tasks/
├── <模块名>/
│   └── <YYYYMMDD>_<功能名>_v<版本号>.json
└── README.md
```

## 文件命名规则

| 组成部分 | 格式 | 说明 |
|----------|------|------|
| `<模块名>` | 小写字母+下划线 | 如 `user`, `order`, `workflow` |
| `<YYYYMMDD>` | 年月日 | 创建日期 |
| `<功能名>` | 小写字母+下划线 | 如 `login`, `query_order` |
| `<版本号>` | v1, v2... | 迭代版本 |

## 任务 JSON 结构

```json
{
  "meta": {
    "name": "功能名称",
    "version": "1.0",
    "date": "YYYY-MM-DD",
    "references": {
      "prd": ["docs/prd/xxx.md"],
      "tech_design": ["docs/tech/xxx.md"]
    }
  },
  "tasks": [
    {
      "id": "T-001",
      "title": "任务标题",
      "type": "feature",
      "priority": "P1",
      "effort": "M",
      "steps": [],
      "acceptance": [],
      "completed": false
    }
  ]
}
```

## 任务类型

| 类型 | 说明 |
|------|------|
| feature | 功能开发 |
| infra | 基础设施 |
| bugfix | 修复 |
| refactor | 重构 |
| test | 测试 |
| docs | 文档 |

## 优先级

| 优先级 | 说明 |
|--------|------|
| P0 | 阻塞其他工作 |
| P1 | 重要 |
| P2 | 一般 |
| P3 | 低优先级 |

## 现有任务

| 模块 | 功能 | 版本 | 任务数 | 预估工时 | 状态 |
|------|------|------|--------|----------|------|
| workorder | 工单查询 | v1.0 | 7 | 8h | 待开始 |
|------|------|------|--------|