"""
LangGraph 流程节点定义
- 意图识别节点
- 参数校验节点
- 普通操作节点
- 高危确认节点
- 工具执行节点
- 结果处理节点
"""
import json
import os
import re
from datetime import datetime
from typing import Any

from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, SystemMessage

from app.common.constants import (
    IntentType,
    OperationType,
    RISK_OPERATIONS,
    RISK_CONFIRM_TEMPLATES,
    RISK_OPERATION_INTERVAL,
    URGE_COOLDOWN_SECONDS,
)
from app.common.exceptions import (
    ParamMissingException,
    RiskOperationDeniedException,
    RiskRateLimitException,
)
from app.common.logger import business_logger, audit_logger, log_audit
from app.agent.state import AgentState

load_dotenv()


def _load_prompt(section: str) -> str:
    """加载 Prompt 文档中指定模块的内容"""
    prompt_path = os.path.join(os.path.dirname(__file__), "..", "..", "prompt", "agent_prompt.md")
    try:
        with open(prompt_path, "r", encoding="utf-8") as f:
            content = f.read()
        # 按模块分割
        sections = content.split("## 模块")
        for s in sections:
            if section in s:
                return "## 模块" + s
        return ""
    except Exception:
        return ""


def _get_llm() -> ChatOpenAI:
    """获取 LLM 实例（支持阿里云百炼平台）"""
    api_key = os.getenv("LLM_API_KEY", "your-dashscope-api-key")
    base_url = os.getenv("LLM_API_BASE", "https://dashscope.aliyuncs.com/compatible-mode/v1")
    model = os.getenv("LLM_MODEL", "qwen-plus")
    
    business_logger.info(f"初始化 LLM 实例", model=model, base_url=base_url)
    
    return ChatOpenAI(
        api_key=api_key,
        base_url=base_url,
        model=model,
        temperature=0.1,
        max_tokens=1024,
    )


def _parse_intent_from_text(text: str) -> dict[str, Any]:
    """从用户文本中解析意图（基于关键词匹配 + LLM 降级方案）"""
    text_lower = text.lower()

    # 关键词匹配规则
    intent_rules: list[tuple[list[str], str, bool]] = [
        (["查工单", "看看工单", "工单状态", "查询工单", "查一下", "工单信息"], IntentType.QUERY, False),
        (["建工单", "创建工单", "提工单", "新建工单", "提交工单"], IntentType.CREATE, False),
        (["催一下", "催办", "加急", "催单", "催工单"], IntentType.URGE, False),
        (["关工单", "关闭工单", "关掉工单"], IntentType.CLOSE, True),
        (["删工单", "删除工单", "删掉工单"], IntentType.DELETE, True),
        (["确认执行", "确认", "确定执行"], IntentType.CONFIRM, False),
        (["取消", "取消操作", "不要了"], IntentType.CANCEL, False),
    ]

    for keywords, intent, is_risk in intent_rules:
        for kw in keywords:
            if kw in text_lower:
                return {
                    "intent": intent,
                    "is_risk": is_risk,
                    "confidence": 0.9,
                }

    return {"intent": IntentType.UNKNOWN, "is_risk": False, "confidence": 0.3}


def _extract_params(text: str, intent: str) -> dict[str, Any]:
    """从用户文本中提取参数"""
    params: dict[str, Any] = {}

    # 提取工单编号（WO开头的编号）
    wo_match = re.search(r"WO\d{12,}", text)
    if wo_match:
        params["workorder_id"] = wo_match.group()

    # 提取创建人
    user_patterns = [
        r"创建人[是为：:\s]*(\S+?)(?:\s|,|，|。|$)",
        r"用户[是为：:\s]*(\S+?)(?:\s|,|，|。|$)",
        r"我是(\S+?)(?:\s|,|，|。|$)",
        r"我的名字[是为：:\s]*(\S+?)(?:\s|,|，|。|$)",
        r"查询(\S+?)的工单",  # 匹配"查询张三的工单"
        r"(\S+?)的工单",  # 匹配"张三的工单"
    ]
    for pattern in user_patterns:
        match = re.search(pattern, text)
        if match:
            params["create_user"] = match.group(1)
            break

    # 根据意图提取特定参数
    if intent == IntentType.CREATE:
        # 提取标题
        title_patterns = [
            r"标题[是为：:\s]*(.+?)(?:\n|,|，|内容|$)",
            r"关于(.+?)的工单",
        ]
        for pattern in title_patterns:
            match = re.search(pattern, text)
            if match:
                params["title"] = match.group(1).strip()
                break

        # 提取内容
        content_patterns = [
            r"内容[是为：:\s]*(.+?)$",
            r"描述[是为：:\s]*(.+?)$",
        ]
        for pattern in content_patterns:
            match = re.search(pattern, text)
            if match:
                params["content"] = match.group(1).strip()
                break

    return params


# ==================== 节点函数 ====================

def intent_recognition_node(state: AgentState) -> dict[str, Any]:
    """意图识别节点"""
    user_message = state.get("user_message", "")
    business_logger.info("意图识别开始", user_message=user_message)

    # 先尝试 LLM 识别，失败则降级为关键词匹配
    try:
        llm = _get_llm()
        system_prompt = _load_prompt("二：意图识别")
        if system_prompt:
            response = llm.invoke([
                SystemMessage(content=system_prompt),
                HumanMessage(content=f"用户输入：{user_message}"),
            ])
            # 尝试解析 JSON
            content = response.content
            # 提取 JSON 部分
            json_match = re.search(r"\{[\s\S]*\}", content)
            if json_match:
                intent_result = json.loads(json_match.group())
                intent = intent_result.get("intent", IntentType.UNKNOWN)
                is_risk = intent_result.get("is_risk", False)
                params = intent_result.get("params", {})
                missing_params = intent_result.get("missing_params", [])
                confidence = intent_result.get("confidence", 0.5)
            else:
                raise ValueError("LLM 返回非 JSON 格式")
        else:
            raise ValueError("Prompt 加载失败")
    except Exception as e:
        business_logger.warning(f"LLM 意图识别降级为关键词匹配: {str(e)}")
        intent_result = _parse_intent_from_text(user_message)
        intent = intent_result["intent"]
        is_risk = intent_result["is_risk"]
        confidence = intent_result["confidence"]
        params = _extract_params(user_message, intent)
        missing_params = []

    # 补充：使用关键词匹配来补充参数（即使 LLM 识别成功也补充）
    extracted_params = _extract_params(user_message, intent)
    params = {**params, **extracted_params}

    # 处理确认/取消意图
    if intent == IntentType.CONFIRM:
        return {
            "intent": state.get("intent", IntentType.UNKNOWN),
            "is_risk": state.get("is_risk", False),
            "confirm_status": "confirmed",
            "need_confirm": False,
        }
    elif intent == IntentType.CANCEL:
        return {
            "intent": state.get("intent", IntentType.UNKNOWN),
            "is_risk": state.get("is_risk", False),
            "confirm_status": "cancelled",
            "need_confirm": False,
        }

    # 合并已有参数
    existing_params = state.get("params", {})
    merged_params = {**existing_params, **params}

    # 确定缺失参数
    if not missing_params:
        missing_params = _check_missing_params(intent, merged_params)

    business_logger.info(
        "意图识别完成",
        intent=intent,
        is_risk=is_risk,
        confidence=confidence,
        params=merged_params,
        missing_params=missing_params,
    )

    return {
        "intent": intent,
        "is_risk": is_risk,
        "confidence": confidence,
        "params": merged_params,
        "missing_params": missing_params,
        "need_confirm": is_risk,
        "confirm_status": "none",
    }


def _check_missing_params(intent: str, params: dict[str, Any]) -> list[str]:
    """检查缺失参数"""
    required_map: dict[str, list[str]] = {
        IntentType.QUERY: ["workorder_id", "create_user"],  # 至少一个
        IntentType.CREATE: ["title", "content", "create_user"],
        IntentType.URGE: ["workorder_id"],
        IntentType.CLOSE: ["workorder_id"],
        IntentType.DELETE: ["workorder_id"],
    }
    required = required_map.get(intent, [])
    missing = []

    for field in required:
        if not params.get(field):
            # 查询工单特殊处理：workorder_id 和 create_user 至少有一个
            if intent == IntentType.QUERY:
                if field == "workorder_id" and params.get("create_user"):
                    continue  # 如果有 create_user，则不需要 workorder_id
                if field == "create_user" and params.get("workorder_id"):
                    continue  # 如果有 workorder_id，则不需要 create_user
            missing.append(field)

    return missing


def param_validation_node(state: AgentState) -> dict[str, Any]:
    """参数校验节点"""
    intent = state.get("intent", "")
    params = state.get("params", {})
    missing_params = state.get("missing_params", [])
    user_id = state.get("user_id", "")
    
    business_logger.info(f"参数校验开始", intent=intent, params=params, missing_params=missing_params, user_id=user_id)

    if intent == IntentType.UNKNOWN:
        return {"response_message": "抱歉，我无法理解您的意图。请尝试：查询工单、新建工单、催办工单、关闭工单、删除工单。"}

    # 查询工单特殊处理：如果用户说"我的工单"，自动使用当前用户
    is_my_workorder = False
    if intent == IntentType.QUERY:
        # 检查 create_user 是否为"我"，如果是则替换为 user_id
        if params.get("create_user") == "我":
            if user_id:
                params["create_user"] = user_id
                is_my_workorder = True
                business_logger.info(f"检测到'我的工单'，使用 user_id 替换", user_id=user_id)
        
        # 如果没有 workorder_id 且没有 create_user，也视为"我的工单"
        if not params.get("workorder_id") and not params.get("create_user"):
            if user_id:
                params["create_user"] = user_id
                is_my_workorder = True
                business_logger.info(f"检测到'我的工单'（无参数），使用 user_id", user_id=user_id)
        
        # 如果是查询"我的工单"，返回特殊标记
        if is_my_workorder:
            missing_params = []
            return {
                "intent": intent,
                "is_risk": state.get("is_risk", False),
                "params": params,
                "missing_params": missing_params,
                "tool_id": "workorder_query",
                "is_my_workorder": True,
            }

    if missing_params:
        # 生成询问缺失参数的消息
        param_names = {
            "workorder_id": "工单编号",
            "title": "工单标题",
            "content": "工单内容",
            "create_user": "创建人姓名",
            "status": "工单状态",
        }
        missing_names = [param_names.get(p, p) for p in missing_params]
        ask_message = f"请提供以下必要信息：{', '.join(missing_names)}"
        return {"response_message": ask_message}

    # 确定工具ID
    tool_id_map: dict[str, str] = {
        IntentType.QUERY: "workorder_query",
        IntentType.CREATE: "workorder_create",
        IntentType.URGE: "workorder_urge",
        IntentType.CLOSE: "workorder_close",
        IntentType.DELETE: "workorder_delete",
    }
    tool_id = tool_id_map.get(intent, "")

    return {"tool_id": tool_id}


def risk_confirm_node(state: AgentState) -> dict[str, Any]:
    """高危操作确认节点"""
    intent = state.get("intent", "")
    is_risk = state.get("is_risk", False)
    confirm_status = state.get("confirm_status", "none")
    params = state.get("params", {})

    # 非高危操作直接通过
    if not is_risk:
        return {"need_confirm": False, "confirm_status": "confirmed"}

    # 高危操作需要确认
    if confirm_status == "none" or confirm_status == "pending":
        # 生成确认话术
        workorder_id = params.get("workorder_id", "未知")
        template = RISK_CONFIRM_TEMPLATES.get(intent, "")
        confirm_message = template.format(workorder_id=workorder_id)
        return {
            "need_confirm": True,
            "confirm_status": "pending",
            "response_message": confirm_message,
        }

    if confirm_status == "cancelled":
        # 用户取消
        audit_logger.info(
            "高危操作已取消",
            session_id=state.get("session_id", ""),
            user_id=state.get("user_id", ""),
            workorder_id=params.get("workorder_id", ""),
            operation_type=intent,
        )
        return {
            "need_confirm": False,
            "confirm_status": "cancelled",
            "response_message": "操作已取消。",
        }

    if confirm_status == "confirmed":
        # 高危操作限流检查
        _check_risk_rate_limit(state)
        return {"need_confirm": False, "confirm_status": "confirmed"}

    return {"need_confirm": True, "confirm_status": "pending"}


def _check_risk_rate_limit(state: AgentState) -> None:
    """高危操作限流检查：同一账号1分钟内禁止重复提交"""
    try:
        import redis as redis_lib
        r = redis_lib.Redis(
            host=os.getenv("REDIS_HOST", "127.0.0.1"),
            port=int(os.getenv("REDIS_PORT", "6379")),
            password=os.getenv("REDIS_PASSWORD") or None,
            db=int(os.getenv("REDIS_DB", "0")),
        )
        user_id = state.get("user_id", "")
        intent = state.get("intent", "")
        rate_key = f"risk_rate:{user_id}:{intent}"
        if r.exists(rate_key):
            raise RiskRateLimitException()
        r.setex(rate_key, RISK_OPERATION_INTERVAL, "1")
    except RiskRateLimitException:
        raise
    except Exception as e:
        business_logger.warning(f"限流检查异常（放行）: {str(e)}")


async def tool_execution_node(state: AgentState) -> dict[str, Any]:
    """工具执行节点：通过 Harness 管控层调用业务服务"""
    tool_id = state.get("tool_id", "")
    params = state.get("params", {})
    session_id = state.get("session_id", "")
    user_id = state.get("user_id", "")
    ip_address = state.get("ip_address", "")

    if not tool_id:
        return {
            "tool_success": False,
            "tool_error_code": "NO_TOOL",
            "tool_error_message": "未匹配到对应工具",
        }

    # 直接调用业务服务层（本地调用，不走 HTTP）
    from app.services.workorder_service import workorder_service

    try:
        result = await workorder_service.execute(tool_id, params, session_id, user_id, ip_address)
        return {
            "tool_result": result,
            "tool_success": True,
        }
    except Exception as e:
        error_code = getattr(e, "error_code", "UNKNOWN_ERROR")
        error_message = getattr(e, "message", str(e))
        # 获取可用用户列表（用于"我的工单"查询失败时提供友好提示）
        available_users = getattr(e, "available_users", [])
        business_logger.error(
            f"工具执行失败: {error_message}",
            tool_id=tool_id,
            error_code=error_code,
        )
        return {
            "tool_success": False,
            "tool_error_code": error_code,
            "tool_error_message": error_message,
            "available_users": available_users,
        }


def result_processing_node(state: AgentState) -> dict[str, Any]:
    """结果处理节点：格式化输出"""
    intent = state.get("intent", "")
    tool_success = state.get("tool_success", False)
    tool_result = state.get("tool_result")
    tool_error_code = state.get("tool_error_code")
    tool_error_message = state.get("tool_error_message")
    params = state.get("params", {})
    available_users = state.get("available_users", [])
    is_my_workorder = state.get("is_my_workorder", False)

    operation_names = {
        IntentType.QUERY: "查询工单",
        IntentType.CREATE: "新建工单",
        IntentType.URGE: "工单催办",
        IntentType.CLOSE: "关闭工单",
        IntentType.DELETE: "删除工单",
    }
    operation_name = operation_names.get(intent, "未知操作")

    if tool_success and tool_result:
        # 成功结果格式化
        message = _format_success_result(intent, tool_result)
        # 高危操作写入审计日志
        if state.get("is_risk"):
            log_audit(
                session_id=state.get("session_id", ""),
                user_id=state.get("user_id", ""),
                workorder_id=params.get("workorder_id", ""),
                operation_type=intent,
                is_risk=True,
                operation_result="成功",
                ip_address=state.get("ip_address", ""),
            )
        return {"response_message": message}
    else:
        # 失败结果格式化
        # 如果是查询"我的工单"失败，提供更友好的提示
        if is_my_workorder and tool_error_code == "WORKORDER_NOT_FOUND" and available_users:
            users_str = "、".join(available_users[:5])
            if len(available_users) > 5:
                users_str += f" 等{len(available_users)}人"
            error_msg = f"【操作结果】\n  操作类型：查询工单\n  执行状态：失败\n  错误描述：当前用户 ({state.get('user_id', '')}) 暂无工单记录\n  可选操作：您可以尝试查询其他用户的工单，如：查询张三的工单、查询李四的工单\n  系统中已有工单的用户：{users_str}"
        else:
            error_msg = _format_error_result(operation_name, tool_error_code, tool_error_message)
        # 高危操作失败也写入审计日志
        if state.get("is_risk"):
            log_audit(
                session_id=state.get("session_id", ""),
                user_id=state.get("user_id", ""),
                workorder_id=params.get("workorder_id", ""),
                operation_type=intent,
                is_risk=True,
                operation_result=f"失败: {tool_error_message}",
                ip_address=state.get("ip_address", ""),
            )
        return {"response_message": error_msg}


def _format_success_result(intent: str, result: dict[str, Any] | list) -> str:
    """格式化成功结果"""
    if intent == IntentType.QUERY:
        if isinstance(result, list):
            lines = ["【查询结果】"]
            for item in result:
                lines.append(f"  工单编号：{item.get('workorder_id', '')}")
                lines.append(f"  标题：{item.get('title', '')}")
                lines.append(f"  状态：{item.get('status', '')}")
                lines.append(f"  创建人：{item.get('create_user', '')}")
                lines.append(f"  创建时间：{item.get('create_time', '')}")
                lines.append("---")
            return "\n".join(lines)
        else:
            return (
                f"【查询结果】\n"
                f"  工单编号：{result.get('workorder_id', '')}\n"
                f"  标题：{result.get('title', '')}\n"
                f"  内容：{result.get('content', '')}\n"
                f"  状态：{result.get('status', '')}\n"
                f"  创建人：{result.get('create_user', '')}\n"
                f"  创建时间：{result.get('create_time', '')}"
            )
    elif intent == IntentType.CREATE:
        return (
            f"【操作结果】\n"
            f"  操作类型：新建工单\n"
            f"  执行状态：成功\n"
            f"  工单编号：{result.get('workorder_id', '')}\n"
            f"  标题：{result.get('title', '')}\n"
            f"  创建时间：{result.get('create_time', '')}"
        )
    elif intent == IntentType.URGE:
        return (
            f"【操作结果】\n"
            f"  操作类型：工单催办\n"
            f"  执行状态：成功\n"
            f"  工单编号：{result.get('workorder_id', '')}\n"
            f"  催办时间：{result.get('urge_time', '')}"
        )
    elif intent == IntentType.CLOSE:
        return (
            f"【操作结果】\n"
            f"  操作类型：关闭工单\n"
            f"  执行状态：成功\n"
            f"  工单编号：{result.get('workorder_id', '')}\n"
            f"  当前状态：已关闭"
        )
    elif intent == IntentType.DELETE:
        return (
            f"【操作结果】\n"
            f"  操作类型：删除工单\n"
            f"  执行状态：成功（软删除，数据可恢复）\n"
            f"  工单编号：{result.get('workorder_id', '')}"
        )
    return "操作成功"


def _format_error_result(operation_name: str, error_code: str | None, error_message: str | None) -> str:
    """格式化错误结果"""
    # 错误码映射为用户友好文案
    error_map = {
        "WORKORDER_NOT_FOUND": "未找到该工单，请检查工单编号是否正确",
        "PARAM_MISSING": "缺少必要参数，请提供完整信息",
        "DUPLICATE_OPERATION": "该操作已执行，请勿重复提交",
        "WORKORDER_STATUS_ERROR": "工单当前状态不允许此操作",
        "RISK_RATE_LIMIT": "操作过于频繁，请1分钟后再试",
        "CIRCUIT_BREAKER_OPEN": "当前服务繁忙，请稍后再试",
        "SERVICE_DEGRADED": "当前服务繁忙，请稍后再试",
    }
    user_message = error_map.get(error_code or "", error_message or "操作失败，请稍后重试")

    return (
        f"【操作结果】\n"
        f"  操作类型：{operation_name}\n"
        f"  执行状态：失败\n"
        f"  错误描述：{user_message}\n"
        f"  建议操作：请检查输入信息后重试，或联系管理员"
    )
