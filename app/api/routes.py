"""
FastAPI 接口层
- POST /api/chat 对话接口
- GET /health 健康检查接口
"""
import uuid
from typing import Any

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
    对话接口：接收用户消息，返回 Agent 结果
    """
    try:
        business_logger.info(
            "收到对话请求",
            session_id=request.session_id,
            user_id=request.user_id,
            user_message=request.message[:100],
        )

        # 构建 Agent 状态
        from app.agent.graph import run_agent
        from app.agent.state import AgentState

        # 从 Redis 加载会话历史
        chat_history = _load_chat_history(request.session_id)

        state: AgentState = {
            "session_id": request.session_id,
            "user_id": request.user_id,
            "ip_address": request.ip_address,
            "user_message": request.message,
            "chat_history": chat_history,
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

        # 运行 Agent
        result = await run_agent(state)

        # 保存会话历史到 Redis
        _save_chat_history(request.session_id, request.message, result.get("response_message", ""))

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


def _load_chat_history(session_id: str) -> list[dict[str, str]]:
    """从 Redis 加载会话历史"""
    try:
        import redis as redis_lib
        import os
        import json

        r = redis_lib.Redis(
            host=os.getenv("REDIS_HOST", "127.0.0.1"),
            port=int(os.getenv("REDIS_PORT", "6379")),
            password=os.getenv("REDIS_PASSWORD") or None,
            db=int(os.getenv("REDIS_DB", "0")),
        )
        history_key = f"chat_history:{session_id}"
        history_data = r.lrange(history_key, -10, -1)  # 最近10条
        return [json.loads(item) for item in history_data]
    except Exception:
        return []


def _save_chat_history(session_id: str, user_message: str, agent_message: str) -> None:
    """保存会话历史到 Redis"""
    try:
        import redis as redis_lib
        import os
        import json

        r = redis_lib.Redis(
            host=os.getenv("REDIS_HOST", "127.0.0.1"),
            port=int(os.getenv("REDIS_PORT", "6379")),
            password=os.getenv("REDIS_PASSWORD") or None,
            db=int(os.getenv("REDIS_DB", "0")),
        )
        history_key = f"chat_history:{session_id}"
        # 保存用户消息和 Agent 回复
        r.rpush(history_key, json.dumps({"role": "user", "content": user_message}, ensure_ascii=False))
        r.rpush(history_key, json.dumps({"role": "assistant", "content": agent_message}, ensure_ascii=False))
        # 设置过期时间 30 分钟
        r.expire(history_key, 1800)
    except Exception as e:
        business_logger.warning(f"保存会话历史失败: {str(e)}")
