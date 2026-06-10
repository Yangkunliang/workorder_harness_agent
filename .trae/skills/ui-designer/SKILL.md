---
name: ui-designer
description: "Use when user wants to design UI/UX for web applications or mobile apps. Calls external UI/UX design Skill (ui-ux-pro-max) to create wireframes, prototypes, and design specifications based on PRD requirements."
---

# UI/UX 设计师（UI Designer）Skill

## 角色定义

作为外部 UI/UX 设计 Skill 的调用入口，负责将用户需求传递给专业的 UI/UX 设计工具（如 ui-ux-pro-max）。

## 执行策略

**纯外部调用模式**：直接调用外部 Skill `ui-ux-pro-max` 进行设计。

```
用户请求设计需求
    ↓
检查外部 Skill (ui-ux-pro-max) 是否可用
    ├── 是 → 调用 `trae run /ui-ux-pro-max --prd xxx.md --output xxx`
    └── 否 → 返回错误提示，建议安装外部 Skill
```

## 工作流程

### 阶段一：需求收集

收集设计需求：
- PRD 文档路径
- 目标模块名称
- 设计风格偏好（可选）

### 阶段二：外部调用

执行命令调用外部 Skill：

```bash
trae run /ui-ux-pro-max \
  --prd docs/prd/<模块名>/<YYYYMMDD>_<功能名>_v<版本号>.md \
  --output docs/ui-design/<模块名>/ \
  --format markdown
```

### 阶段三：结果处理

1. 检查输出文件是否生成成功
2. 更新 `docs/ui-design/README.md` 索引
3. 返回设计文档路径给用户

## 错误处理

如果外部 Skill 不可用：

```
错误提示：
- 请检查是否已安装 ui-ux-pro-max Skill
- 安装命令：trae skills install ui-ux-pro-max
- 或使用：trae skills list 查看已安装的 Skill
```

## 输出格式

设计文档输出路径：
```
docs/ui-design/<模块名>/<YYYYMMDD>_<页面名>_design_v<版本号>.md
```

## 重要规则

1. **外部优先**：始终调用外部专业设计工具
2. **透明传递**：将用户需求完整传递给外部 Skill
3. **错误反馈**：清晰告知用户外部 Skill 的安装状态