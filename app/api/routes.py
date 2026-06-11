"""
FastAPI 接口层
- POST /api/chat 对话接口
- GET /health 健康检查接口
- GET /api/workorder 工单查询接口
- GET /api/workorder/{workorder_no} 工单详情接口
"""
from datetime import datetime, timedelta
from fastapi import APIRouter, HTTPException, Query

from app.schemas.request import ChatRequest
from app.schemas.response import ChatResponse, ApiResponse
from app.schemas.workorder import (
    WorkorderQueryRequest,
    WorkorderResponse,
    WorkorderDetailResponse,
    PaginationResponse,
    WorkorderListResponse,
)
from app.common.constants import ErrorCode, ERROR_MESSAGES
from app.common.exceptions import BaseAppException, WorkorderNotFoundException
from app.common.logger import business_logger
from app.services.workorder_service import workorder_service

router = APIRouter()


@router.get("/api/workorder", response_model=ApiResponse)
async def workorder_list(
    page: int = Query(1, ge=1, description="页码（从1开始）"),
    size: int = Query(20, ge=1, le=100, description="每页条数（最大100）"),
    workorder_no: str = Query(None, description="工单编号（支持逗号分隔多个）"),
    creator: str = Query(None, description="创建人（前缀匹配）"),
    start_date: str = Query(None, description="开始日期（格式：YYYY-MM-DD）"),
    end_date: str = Query(None, description="结束日期（格式：YYYY-MM-DD）"),
) -> ApiResponse:
    """
    查询工单列表
    
    支持按工单编号、创建人、时间范围等条件查询，默认查询最近7天的工单。
    """
    try:
        # 构建查询条件
        filters = {}
        if workorder_no:
            filters["workorder_no"] = workorder_no
        if creator:
            filters["creator"] = creator
        
        # 设置默认时间范围（最近7天）
        if not start_date:
            start_date = (datetime.now() - timedelta(days=7)).strftime("%Y-%m-%d")
        filters["start_date"] = start_date
        
        if end_date:
            filters["end_date"] = end_date
        
        # 调用服务层
        result = await workorder_service.query_workorder(
            filters=filters,
            page=page,
            size=size,
            desensitize=True
        )
        
        business_logger.info(
            "工单列表查询成功",
            filters=filters,
            page=page,
            size=size,
            total=result["pagination"]["total"]
        )
        
        return ApiResponse.success(data=result)
    
    except BaseAppException as e:
        business_logger.error(f"业务异常: {e.message}", error_code=e.error_code)
        return ApiResponse.error(code=e.error_code, message=e.message)
    except Exception as e:
        business_logger.error(f"工单列表查询异常: {str(e)}")
        return ApiResponse.error(
            code=ErrorCode.UNKNOWN_ERROR,
            message=ERROR_MESSAGES.get(ErrorCode.UNKNOWN_ERROR, "未知错误"),
        )


@router.get("/api/workorder/{workorder_no}", response_model=ApiResponse)
async def workorder_detail(workorder_no: str) -> ApiResponse:
    """
    查询工单详情
    
    返回工单的完整信息（不脱敏）。
    """
    try:
        # 调用服务层
        result = await workorder_service.get_workorder_detail(workorder_no=workorder_no)
        
        business_logger.info(f"工单详情查询成功: {workorder_no}")
        
        return ApiResponse.success(data=result)
    
    except WorkorderNotFoundException as e:
        business_logger.warning(f"工单不存在: {workorder_no}")
        return ApiResponse.error(code="10002", message="工单不存在")
    except BaseAppException as e:
        business_logger.error(f"业务异常: {e.message}", error_code=e.error_code)
        return ApiResponse.error(code=e.error_code, message=e.message)
    except Exception as e:
        business_logger.error(f"工单详情查询异常: {str(e)}")
        return ApiResponse.error(
            code=ErrorCode.UNKNOWN_ERROR,
            message=ERROR_MESSAGES.get(ErrorCode.UNKNOWN_ERROR, "未知错误"),
        )


@router.get("/health", response_model=ApiResponse)
async def health_check() -> ApiResponse:
    """健康检查接口"""
    return ApiResponse.success(data={"status": "healthy", "service": "workorder-harness-agent"})


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

        return ApiResponse.success(
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
        return ApiResponse.error(code=e.error_code, message=e.message)
    except Exception as e:
        business_logger.error(f"未知异常: {str(e)}")
        return ApiResponse.error(
            code=ErrorCode.UNKNOWN_ERROR,
            message=ERROR_MESSAGES.get(ErrorCode.UNKNOWN_ERROR, "未知错误"),
        )
