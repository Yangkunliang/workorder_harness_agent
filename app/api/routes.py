"""
FastAPI 接口层
- POST /api/chat 对话接口
- GET /health 健康检查接口
"""
from fastapi import APIRouter, HTTPException

from app.schemas.request import ChatRequest
from app.schemas.response import ChatResponse, ApiResponse
from app.common.constants import ErrorCode, ERROR_MESSAGES
from app.common.exceptions import BaseAppException
from app.common.logger import business_logger

router = APIRouter()


@router.get("/health")
async def health_check() -> dict[str, str]:
    """健康检查接口"""
    return {"status": "healthy", "service": "workorder-harness-agent"}


@router.post("/api/chat", response_model=ApiResponse)
async def chat(request: ChatRequest) -> ApiResponse:
    """
    对话接口：接收用户消息，返回 Agent 结果。

    会话历史由 LangGraph checkpointer（AsyncRedisSaver）自动管理：
    - 以 session_id 作为 thread_id
    - 每次调用自动从 Redis 恢复上一轮 checkpoint，执行后自动持久化
    - 无需手动 load/save chat_history
    """
    try:
        business_logger.info(
            "收到对话请求",
            session_id=request.session_id,
            user_id=request.user_id,
            user_message=request.message[:100],
        )

        from app.agent.graph import run_agent
        from app.agent.state import AgentState

        # 构建本轮输入状态（仅当前轮次字段，历史由 checkpointer 自动注入）
        state: AgentState = {
            "session_id": request.session_id,
            "user_id": request.user_id,
            "ip_address": request.ip_address,
            "user_message": request.message,
            "intent": "",
            "is_risk": False,
            "confidence": 0.0,
            "params": {},
            "missing_params": [],
            "need_confirm": False,
            "confirm_status": "none",
            "tool_id": "",
            "tool_result": None,
            "tool_success": False,
            "tool_error_code": None,
            "tool_error_message": None,
            "response_message": "",
        }

        # 运行 Agent（checkpointer 自动处理会话历史的恢复与持久化）
        result = await run_agent(request.session_id, state)

        return ApiResponse(
            code=ErrorCode.SUCCESS,
            message="操作成功",
            data=ChatResponse(
                session_id=request.session_id,
                message=result.get("response_message", ""),
                intent=result.get("intent"),
                need_confirm=result.get("need_confirm", False),
                data=result.get("tool_result"),
            ),
        )

    except BaseAppException as e:
        business_logger.error(f"业务异常: {e.message}", error_code=e.error_code)
        return ApiResponse(
            code=e.error_code,
            message=e.message,
            data=None,
        )
    except Exception as e:
        business_logger.error(f"未知异常: {str(e)}")
        return ApiResponse(
            code=ErrorCode.UNKNOWN_ERROR,
            message=ERROR_MESSAGES.get(ErrorCode.UNKNOWN_ERROR, "未知错误"),
            data=None,
        )
