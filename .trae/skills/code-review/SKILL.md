# Code Review Skill

## 概述

代码审查 Skill，用于分析测试失败原因并尝试自动修复代码问题。

## 功能

- 分析单元测试失败的错误信息
- 识别常见代码问题（语法错误、逻辑错误、测试用例问题）
- 自动修复简单的代码问题
- 生成修复报告

## 工作流程

### 输入
```json
{
  "test_output": "测试失败的详细输出",
  "failed_tests": ["测试用例1", "测试用例2"],
  "error_details": "错误堆栈信息",
  "retry_count": 1,
  "max_retries": 5
}
```

### 输出
```json
{
  "fixed": true,
  "fixed_files": ["app/utils/desensitize.py"],
  "fix_summary": "修复了姓名脱敏函数的边界条件处理",
  "suggestion": "建议检查其他测试用例",
  "retry_count": 2
}
```

## 支持的修复类型

| 修复类型 | 说明 | 示例 |
|----------|------|------|
| assertion_failure | 断言失败 | 测试期望值与实际值不匹配 |
| type_error | 类型错误 | 参数类型不匹配 |
| value_error | 值错误 | 无效参数值 |
| import_error | 导入错误 | 模块或类不存在 |
| index_error | 索引错误 | 列表越界访问 |
| key_error | 键错误 | 字典键不存在 |
| boundary_condition | 边界条件 | 空字符串、None 值处理 |

## 使用方式

```bash
# 执行代码审查
trae run /code-review

# 带参数执行
trae run /code-review --input '{"test_output": "...", "failed_tests": [...]}'
```

## 配置

```json
{
  "auto_fix_enabled": true,
  "max_fix_attempts": 3,
  "backup_before_fix": true,
  "notify_on_fix": true
}
```

## 依赖工具

- Python 3.8+
- pytest（测试框架）
- ast（Python 语法分析）

## 示例

### 场景：测试失败
```
FAILED tests/unit/test_desensitize.py::TestDesensitizeName::test_empty_string
AssertionError: assert '' == ' *'
```

### 自动修复
1. 分析错误：空字符串脱敏后应为空字符串
2. 定位问题：desensitize_name 函数缺少空字符串检查
3. 修复代码：添加 strip 后的空字符串检查
4. 生成修复报告

## 注意事项

1. 自动修复仅适用于简单的代码问题
2. 复杂逻辑错误需要人工审查
3. 修复前会自动备份原始文件
4. 超过最大修复次数后停止自动修复

## 版本历史

| 版本 | 日期 | 更新内容 |
|------|------|----------|
| 1.0 | 2026-06-11 | 初始版本，支持基础修复 |
