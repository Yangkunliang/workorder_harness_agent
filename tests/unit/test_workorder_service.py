"""
工单服务层单元测试
测试 app/services/workorder_service.py 中的服务方法
"""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime

from app.services.workorder_service import WorkorderService


class TestWorkorderServiceDesensitize:
    """工单服务脱敏功能测试"""

    def setup_method(self):
        """每个测试方法前初始化服务实例"""
        self.service = WorkorderService()

    def test_desensitize_single_char_name(self):
        """测试单字符姓名脱敏"""
        result = self.service._desensitize_creator("李")
        assert result == "李*"

    def test_desensitize_two_char_name(self):
        """测试双字符姓名脱敏"""
        result = self.service._desensitize_creator("张三")
        assert result == "张*"

    def test_desensitize_three_char_name(self):
        """测试三字符姓名脱敏"""
        result = self.service._desensitize_creator("张三丰")
        assert result == "张*丰"

    def test_desensitize_four_char_name(self):
        """测试四字符姓名脱敏"""
        result = self.service._desensitize_creator("欧阳锋")
        assert result == "欧*锋"


class TestWorkorderServiceCacheKey:
    """工单服务缓存键生成测试"""

    def setup_method(self):
        """每个测试方法前初始化服务实例"""
        self.service = WorkorderService()

    def test_cache_key_with_empty_filters(self):
        """测试空过滤条件生成缓存键"""
        key1 = self.service._get_cache_key({}, 1, 20)
        key2 = self.service._get_cache_key({}, 1, 20)
        assert key1 == key2
        assert key1.startswith("workorder:query:")

    def test_cache_key_with_different_filters(self):
        """测试不同过滤条件生成不同缓存键"""
        key1 = self.service._get_cache_key({"creator": "张"}, 1, 20)
        key2 = self.service._get_cache_key({"creator": "李"}, 1, 20)
        assert key1 != key2

    def test_cache_key_with_different_page(self):
        """测试不同页码生成不同缓存键"""
        key1 = self.service._get_cache_key({}, 1, 20)
        key2 = self.service._get_cache_key({}, 2, 20)
        assert key1 != key2

    def test_cache_key_with_different_size(self):
        """测试不同页大小生成不同缓存键"""
        key1 = self.service._get_cache_key({}, 1, 20)
        key2 = self.service._get_cache_key({}, 1, 50)
        assert key1 != key2

    def test_cache_key_deterministic(self):
        """测试缓存键生成是确定性的"""
        filters = {"workorder_no": "WO001", "creator": "张三"}
        key1 = self.service._get_cache_key(filters, 1, 20)
        key2 = self.service._get_cache_key(filters, 1, 20)
        key3 = self.service._get_cache_key(filters, 1, 20)
        assert key1 == key2 == key3


class TestWorkorderServiceRedisClient:
    """工单服务 Redis 客户端测试"""

    def setup_method(self):
        """每个测试方法前初始化服务实例"""
        self.service = WorkorderService()

    def test_get_redis_client_returns_none_on_error(self):
        """测试 Redis 连接失败时返回 None"""
        with patch.dict("os.environ", {"REDIS_HOST": "invalid-host"}):
            with patch("redis.Redis") as mock_redis:
                mock_redis.side_effect = Exception("Connection failed")
                client = self.service._get_redis_client()
                # 应该返回 None 而不是抛出异常
                assert client is None


class TestWorkorderServiceDictConversion:
    """工单服务字典转换测试"""

    def setup_method(self):
        """每个测试方法前初始化服务实例"""
        self.service = WorkorderService()
        
        # 创建模拟的 Workorder 对象
        self.mock_workorder = MagicMock()
        self.mock_workorder.workorder_no = "WO202506100001"
        self.mock_workorder.title = "测试工单"
        self.mock_workorder.status = "pending"
        self.mock_workorder.creator = "张三丰"
        self.mock_workorder.description = "这是一个测试工单"
        self.mock_workorder.created_at = datetime(2025, 6, 10, 10, 0, 0)
        self.mock_workorder.updated_at = datetime(2025, 6, 10, 14, 30, 0)

    def test_to_dict_with_desensitize(self):
        """测试转换为字典（带脱敏）"""
        result = self.service._to_dict_with_desensitize(self.mock_workorder, desensitize=True)
        
        assert result["workorder_no"] == "WO202506100001"
        assert result["title"] == "测试工单"
        assert result["status"] == "pending"
        assert result["creator"] == "张*丰"  # 应该被脱敏
        assert "created_at" in result
        assert "updated_at" in result

    def test_to_dict_without_desensitize(self):
        """测试转换为字典（不脱敏）"""
        result = self.service._to_dict_with_desensitize(self.mock_workorder, desensitize=False)
        
        assert result["workorder_no"] == "WO202506100001"
        assert result["title"] == "测试工单"
        assert result["status"] == "pending"
        assert result["creator"] == "张三丰"  # 不脱敏
        assert "created_at" in result
        assert "updated_at" in result

    def test_to_detail_dict(self):
        """测试转换为详情字典"""
        result = self.service._to_detail_dict(self.mock_workorder)
        
        assert result["workorder_no"] == "WO202506100001"
        assert result["title"] == "测试工单"
        assert result["status"] == "pending"
        assert result["creator"] == "张三丰"  # 详情不脱敏
        assert result["description"] == "这是一个测试工单"
        assert "created_at" in result
        assert "updated_at" in result

    def test_to_detail_dict_with_empty_description(self):
        """测试转换为详情字典（空描述）"""
        self.mock_workorder.description = None
        result = self.service._to_detail_dict(self.mock_workorder)
        
        assert result["description"] == ""


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
