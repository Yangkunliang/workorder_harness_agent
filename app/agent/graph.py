"""
LangGraph 状态机流程图
- 定义节点和边
- 分支判断逻辑
- 流程组装
- 使用 AsyncRedisSaver 作为 checkpointer，实现多轮会话持久化
"""
from typing import Any

from langgraph.graph import StateGraph, END

from app.agent.state import AgentState
from app.agent.nodes import (
    intent_recognition_node,
    param_validation_node,
    risk_confirm_node,
    tool_execution_node,
    result_processing_node,
)
from app.common.constants import IntentType
from app.common.logger import business_logger


# ==================== 分支判断函数 ====================

def should_ask_params(state: AgentState) -> str:
    """判断是否需要询问缺失参数"""
    missing_params = state.get("missing_params", [])
    intent = state.get("intent", "")

    if intent == IntentType.UNKNOWN:
        return "result"

    if missing_params:
        return "result"

    return "risk_confirm"


def should_confirm_risk(state: AgentState) -> str:
    """判断高危操作是否需要确认"""
    is_risk = state.get("is_risk", False)
    need_confirm = state.get("need_confirm", True)
    confirm_status = state.get("confirm_status", "none")

    if not is_risk:
        return "execute"

    if confirm_status == "confirmed":
        return "execute"
    elif confirm_status == "cancelled":
        return "result"
    else:
        # 需要确认
        return "wait_confirm"


def should_execute_after_confirm(state: AgentState) -> str:
    """确认后的分支判断"""
    confirm_status = state.get("confirm_status", "none")

    if confirm_status == "confirmed":
        return "execute"
    elif confirm_status == "cancelled":
        return "result"
    else:
        return "result"


# ==================== 构建状态机 ====================

def build_agent_graph() -> StateGraph:
    """构建 Agent 状态机流程图"""
    workflow = StateGraph(AgentState)

    # 添加节点
    workflow.add_node("intent_recognition", intent_recognition_node)
    workflow.add_node("param_validation", param_validation_node)
    workflow.add_node("risk_confirm", risk_confirm_node)
    workflow.add_node("tool_execution", tool_execution_node)
    workflow.add_node("result_processing", result_processing_node)

    # 设置入口
    workflow.set_entry_point("intent_recognition")

    # 意图识别 → 参数校验
    workflow.add_edge("intent_recognition", "param_validation")

    # 参数校验 → 分支判断
    workflow.add_conditional_edges(
        "param_validation",
        should_ask_params,
        {
            "risk_confirm": "risk_confirm",
            "result": "result_processing",
        },
    )

    # 高危确认 → 分支判断
    workflow.add_conditional_edges(
        "risk_confirm",
        should_confirm_risk,
        {
            "wait_confirm": "result_processing",  # 输出确认话术，等待用户回复
            "execute": "tool_execution",
            "result": "result_processing",
        },
    )

    # 工具执行 → 结果处理
    workflow.add_edge("tool_execution", "result_processing")

    # 结果处理 → 结束
    workflow.add_edge("result_processing", END)

    return workflow


# ==================== 编译图（注入 checkpointer） ====================

def _build_compiled_graph():
    """
    编译 Agent 图并注入 AsyncRedisSaver checkpointer。
    checkpointer 以 thread_id（即 session_id）为 key，自动完成：
      - 每次调用前从 Redis 恢复上一轮 checkpoint
      - 每次调用后将完整 state 持久化回 Redis
    """
    from langgraph.checkpoint.redis.aio import AsyncRedisSaver
    from app.database.redis_client import get_redis_client

    checkpointer = AsyncRedisSaver(redis_client=get_redis_client())
    return build_agent_graph().compile(checkpointer=checkpointer)


agent_graph = _build_compiled_graph()


async def setup_checkpointer() -> None:
    """
    初始化 checkpointer 所需的 Redis 索引结构。
    必须在服务启动阶段（lifespan）调用一次，否则首次写入会报错。
    """
    await agent_graph.checkpointer.asetup()


async def run_agent(session_id: str, state: AgentState) -> dict[str, Any]:
    """
    运行 Agent 状态机。

    Args:
        session_id: 会话 ID，作为 checkpointer 的 thread_id
        state: 本轮输入状态（仅包含当前轮次的增量字段）

    Returns:
        执行完成后的完整 state dict
    """
    config = {"configurable": {"thread_id": session_id}}

    business_logger.info(
        "Agent 执行开始",
        session_id=session_id,
        user_message=state.get("user_message", ""),
    )

    result = await agent_graph.ainvoke(state, config=config)

    business_logger.info(
        "Agent 执行完成",
        session_id=session_id,
        response_message=result.get("response_message", "")[:100],
    )

    return result
