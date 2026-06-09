"""
LangGraph 状态定义
- 会话状态管理
- 意图、参数、确认状态等
"""
from typing import Any, Optional
from typing_extensions import TypedDict


class AgentState(TypedDict, total=False):
    """Agent 状态机状态定义"""
    # 会话信息
    session_id: str
    user_id: str
    ip_address: str
    user_message: str

    # 意图识别结果
    intent: str
    is_risk: bool
    confidence: float

    # 参数信息
    params: dict[str, Any]
    missing_params: list[str]

    # 高危操作确认状态
    need_confirm: bool
    confirm_status: str  # pending / confirmed / cancelled / none

    # 工具执行结果
    tool_id: str
    tool_result: Optional[dict[str, Any]]
    tool_success: bool
    tool_error_code: Optional[str]
    tool_error_message: Optional[str]
    available_users: list[str]

    # 标记查询"我的工单"
    is_my_workorder: bool

    # 最终输出
    response_message: str

    # 历史消息（用于 LLM 上下文）
    chat_history: list[dict[str, str]]
