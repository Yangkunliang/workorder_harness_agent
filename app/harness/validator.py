"""
输入校验层（Harness 第1层）
- 基于 Pydantic 强类型 + Schema 校验
- 参数缺失检测
- 非法参数拦截
"""
from typing import Any

from app.common.exceptions import (
    ValidationException,
    ParamMissingException,
    IllegalParamException,
)
from app.common.logger import business_logger
from app.schemas.tool_schema import ToolExecutionRequest


class InputValidator:
    """输入校验器：基于工具 Schema 对入参进行强类型校验"""

    def validate(self, request: ToolExecutionRequest) -> dict[str, Any]:
        """
        校验工具执行请求
        返回校验通过的参数字典
        """
        tool_id = request.tool_id
        params = request.params

        # 基础校验：tool_id 不能为空
        if not tool_id:
            raise ValidationException("工具ID不能为空")

        # 从注册中心获取工具 Schema
        from app.harness.registry import tool_registry
        tool_config = tool_registry.get_tool(tool_id)
        if not tool_config:
            raise ValidationException(f"未注册的工具：{tool_id}")

        if tool_config.status != "active":
            raise ValidationException(f"工具 {tool_id} 当前不可用")

        # 获取请求参数 Schema
        request_schema = tool_config.request_schema
        required_fields = request_schema.get("required", [])
        properties = request_schema.get("properties", {})

        # 校验必填参数
        validated_params: dict[str, Any] = {}
        for field in required_fields:
            if field not in params or params[field] is None or str(params[field]).strip() == "":
                raise ParamMissingException(field)

        # 校验参数类型和约束
        for key, value in params.items():
            if key not in properties:
                # 允许额外参数通过，但记录警告
                business_logger.warning(f"工具 {tool_id} 收到未定义参数: {key}")
                validated_params[key] = value
                continue

            prop_def = properties[key]
            expected_type = prop_def.get("type", "string")

            # 类型校验
            if expected_type == "string" and not isinstance(value, str):
                validated_params[key] = str(value)
            elif expected_type == "integer" and not isinstance(value, int):
                try:
                    validated_params[key] = int(value)
                except (ValueError, TypeError):
                    raise IllegalParamException(f"参数 {key} 应为整数类型")
            elif expected_type == "number" and not isinstance(value, (int, float)):
                try:
                    validated_params[key] = float(value)
                except (ValueError, TypeError):
                    raise IllegalParamException(f"参数 {key} 应为数值类型")
            elif expected_type == "boolean" and not isinstance(value, bool):
                if str(value).lower() in ("true", "1", "yes"):
                    validated_params[key] = True
                elif str(value).lower() in ("false", "0", "no"):
                    validated_params[key] = False
                else:
                    raise IllegalParamException(f"参数 {key} 应为布尔类型")
            else:
                validated_params[key] = value

            # 字符串长度校验
            if isinstance(validated_params[key], str):
                max_length = prop_def.get("maxLength")
                min_length = prop_def.get("minLength", 0)
                if max_length and len(validated_params[key]) > max_length:
                    raise IllegalParamException(f"参数 {key} 长度不能超过 {max_length}")
                if len(validated_params[key]) < min_length:
                    raise IllegalParamException(f"参数 {key} 长度不能少于 {min_length}")

        business_logger.info(
            "输入校验通过",
            tool_id=tool_id,
            params=list(validated_params.keys()),
        )
        return validated_params


# 全局校验器实例
input_validator = InputValidator()
