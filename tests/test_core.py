"""
单元测试 - 核心流程、参数校验、容错逻辑
"""
import pytest
from unittest.mock import patch, MagicMock

from app.common.constants import IntentType, OperationType, ErrorCode, RISK_OPERATIONS
from app.common.exceptions import (
    ValidationException,
    ParamMissingException,
    IllegalParamException,
    WorkorderNotFoundException,
    DuplicateOperationException,
    RiskOperationDeniedException,
    RiskRateLimitException,
    WorkorderStatusException,
    CircuitBreakerOpenException,
    ServiceDegradedException,
)
from app.agent.nodes import (
    _parse_intent_from_text,
    _extract_params,
    _check_missing_params,
    intent_recognition_node,
    param_validation_node,
    risk_confirm_node,
)


# ==================== 意图识别测试 ====================

class TestIntentRecognition:
    """意图识别测试"""

    def test_query_intent(self) -> None:
        result = _parse_intent_from_text("查询工单")
        assert result["intent"] == IntentType.QUERY
        assert result["is_risk"] is False

    def test_create_intent(self) -> None:
        result = _parse_intent_from_text("创建工单")
        assert result["intent"] == IntentType.CREATE
        assert result["is_risk"] is False

    def test_urge_intent(self) -> None:
        result = _parse_intent_from_text("催办工单")
        assert result["intent"] == IntentType.URGE
        assert result["is_risk"] is False

    def test_close_intent_is_risk(self) -> None:
        result = _parse_intent_from_text("关闭工单")
        assert result["intent"] == IntentType.CLOSE
        assert result["is_risk"] is True

    def test_delete_intent_is_risk(self) -> None:
        result = _parse_intent_from_text("删除工单")
        assert result["intent"] == IntentType.DELETE
        assert result["is_risk"] is True

    def test_confirm_intent(self) -> None:
        result = _parse_intent_from_text("确认执行")
        assert result["intent"] == IntentType.CONFIRM

    def test_cancel_intent(self) -> None:
        result = _parse_intent_from_text("取消")
        assert result["intent"] == IntentType.CANCEL

    def test_unknown_intent(self) -> None:
        result = _parse_intent_from_text("今天天气怎么样")
        assert result["intent"] == IntentType.UNKNOWN


# ==================== 参数提取测试 ====================

class TestParamExtraction:
    """参数提取测试"""

    def test_extract_workorder_id(self) -> None:
        params = _extract_params("查询工单 WO202606090001", IntentType.QUERY)
        assert params.get("workorder_id") == "WO202606090001"

    def test_extract_create_user(self) -> None:
        params = _extract_params("我是张三，查一下我的工单", IntentType.QUERY)
        assert params.get("create_user") == "张三"

    def test_extract_title(self) -> None:
        params = _extract_params("创建工单，标题：服务器告警，内容：CPU过高，创建人：张三", IntentType.CREATE)
        assert "title" in params or "服务器告警" in params.get("title", "")


# ==================== 缺失参数检测测试 ====================

class TestMissingParams:
    """缺失参数检测测试"""

    def test_create_missing_all(self) -> None:
        missing = _check_missing_params(IntentType.CREATE, {})
        assert "title" in missing
        assert "content" in missing
        assert "create_user" in missing

    def test_create_partial(self) -> None:
        missing = _check_missing_params(IntentType.CREATE, {"title": "测试"})
        assert "title" not in missing
        assert "content" in missing

    def test_urge_missing_id(self) -> None:
        missing = _check_missing_params(IntentType.URGE, {})
        assert "workorder_id" in missing

    def test_query_with_id_no_missing(self) -> None:
        missing = _check_missing_params(IntentType.QUERY, {"workorder_id": "WO202606090001"})
        assert len(missing) == 0

    def test_query_needs_at_least_one(self) -> None:
        missing = _check_missing_params(IntentType.QUERY, {})
        assert len(missing) > 0


# ==================== 异常体系测试 ====================

class TestExceptions:
    """异常体系测试"""

    def test_validation_exception(self) -> None:
        exc = ValidationException("参数错误")
        assert exc.error_code == "VALIDATION_ERROR"
        assert "参数错误" in exc.message

    def test_param_missing_exception(self) -> None:
        exc = ParamMissingException("workorder_id")
        assert exc.error_code == "PARAM_MISSING"
        assert "workorder_id" in exc.message

    def test_workorder_not_found(self) -> None:
        exc = WorkorderNotFoundException("WO001")
        assert exc.error_code == "WORKORDER_NOT_FOUND"
        assert "WO001" in exc.message

    def test_risk_operation_denied(self) -> None:
        exc = RiskOperationDeniedException()
        assert exc.error_code == "RISK_OPERATION_DENIED"

    def test_circuit_breaker_open(self) -> None:
        exc = CircuitBreakerOpenException("workorder_close")
        assert exc.error_code == "CIRCUIT_BREAKER_OPEN"


# ==================== 常量校验测试 ====================

class TestConstants:
    """常量校验测试"""

    def test_risk_operations(self) -> None:
        assert OperationType.CLOSE in RISK_OPERATIONS
        assert OperationType.DELETE in RISK_OPERATIONS
        assert OperationType.QUERY not in RISK_OPERATIONS

    def test_error_code_format(self) -> None:
        for code in ErrorCode:
            assert len(code.value) == 5

    def test_intent_type_values(self) -> None:
        assert IntentType.QUERY == "query_workorder"
        assert IntentType.CREATE == "create_workorder"
        assert IntentType.CLOSE == "close_workorder"
        assert IntentType.DELETE == "delete_workorder"


# ==================== 参数校验节点测试 ====================

class TestParamValidationNode:
    """参数校验节点测试"""

    def test_unknown_intent_returns_message(self) -> None:
        state = {
            "intent": IntentType.UNKNOWN,
            "params": {},
            "missing_params": [],
        }
        result = param_validation_node(state)
        assert "无法理解" in result.get("response_message", "")

    def test_missing_params_returns_ask(self) -> None:
        state = {
            "intent": IntentType.CREATE,
            "params": {},
            "missing_params": ["title", "content", "create_user"],
        }
        result = param_validation_node(state)
        assert "请提供" in result.get("response_message", "")

    def test_valid_params_returns_tool_id(self) -> None:
        state = {
            "intent": IntentType.QUERY,
            "params": {"workorder_id": "WO202606090001"},
            "missing_params": [],
        }
        result = param_validation_node(state)
        assert result.get("tool_id") == "workorder_query"


# ==================== 高危确认节点测试 ====================

class TestRiskConfirmNode:
    """高危确认节点测试"""

    def test_normal_operation_passes(self) -> None:
        state = {
            "intent": IntentType.QUERY,
            "is_risk": False,
            "confirm_status": "none",
            "params": {},
        }
        result = risk_confirm_node(state)
        assert result["need_confirm"] is False
        assert result["confirm_status"] == "confirmed"

    def test_risk_operation_needs_confirm(self) -> None:
        state = {
            "intent": IntentType.CLOSE,
            "is_risk": True,
            "confirm_status": "none",
            "params": {"workorder_id": "WO001"},
        }
        result = risk_confirm_node(state)
        assert result["need_confirm"] is True
        assert result["confirm_status"] == "pending"

    def test_risk_cancelled(self) -> None:
        state = {
            "intent": IntentType.CLOSE,
            "is_risk": True,
            "confirm_status": "cancelled",
            "params": {"workorder_id": "WO001"},
        }
        result = risk_confirm_node(state)
        assert result["confirm_status"] == "cancelled"
        assert "取消" in result.get("response_message", "")


# ==================== Pydantic Schema 测试 ====================

class TestSchemas:
    """Pydantic Schema 测试"""

    def test_chat_request_valid(self) -> None:
        from app.schemas.request import ChatRequest
        req = ChatRequest(
            session_id="test-001",
            user_id="user001",
            message="查询工单",
        )
        assert req.session_id == "test-001"

    def test_chat_request_missing_field(self) -> None:
        from app.schemas.request import ChatRequest
        from pydantic import ValidationError
        with pytest.raises(ValidationError):
            ChatRequest(session_id="test-001")

    def test_workorder_create_request_validation(self) -> None:
        from app.schemas.request import WorkorderCreateRequest
        from pydantic import ValidationError
        # 空标题应校验失败
        with pytest.raises(ValidationError):
            WorkorderCreateRequest(title="", content="测试", create_user="张三")

    def test_api_response_default(self) -> None:
        from app.schemas.response import ApiResponse
        resp = ApiResponse()
        assert resp.code == ErrorCode.SUCCESS

    def test_tool_config_model(self) -> None:
        from app.schemas.tool_schema import ToolConfig
        config = ToolConfig(
            tool_id="test_tool",
            tool_name="测试工具",
            target_url="/api/test",
        )
        assert config.tool_id == "test_tool"
        assert config.timeout == 5000
        assert config.max_retry == 2
