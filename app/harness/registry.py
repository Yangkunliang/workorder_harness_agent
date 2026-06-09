"""
工具注册中心（Harness 第3层）
- 对接 Nacos 存储所有工具元数据
- 内存缓存 + 动态刷新
- 提供工具查询、状态管理能力
"""
from typing import Any, Optional

from app.common.logger import business_logger
from app.config.nacos_config import nacos_manager
from app.schemas.tool_schema import ToolConfig


class ToolRegistry:
    """工具注册中心：管理工具元数据的注册、查询、刷新"""

    def __init__(self) -> None:
        self._tools: dict[str, ToolConfig] = {}

    async def init(self) -> None:
        """从 Nacos 加载工具配置到内存缓存"""
        all_tools = nacos_manager.get_all_tools()
        for tool_id, config_dict in all_tools.items():
            self._tools[tool_id] = ToolConfig(**config_dict)
        business_logger.info(f"工具注册中心初始化完成，共 {len(self._tools)} 个工具")

    def get_tool(self, tool_id: str) -> Optional[ToolConfig]:
        """根据 tool_id 获取工具配置"""
        return self._tools.get(tool_id)

    def get_all_tools(self) -> dict[str, ToolConfig]:
        """获取所有工具配置"""
        return self._tools.copy()

    def is_tool_active(self, tool_id: str) -> bool:
        """检查工具是否可用"""
        tool = self._tools.get(tool_id)
        return tool is not None and tool.status == "active"

    def get_tool_timeout(self, tool_id: str) -> int:
        """获取工具超时时间"""
        tool = self._tools.get(tool_id)
        return tool.timeout if tool else 5000

    def get_tool_max_retry(self, tool_id: str) -> int:
        """获取工具最大重试次数"""
        tool = self._tools.get(tool_id)
        return tool.max_retry if tool else 0

    def get_tool_circuit_threshold(self, tool_id: str) -> int:
        """获取工具熔断阈值"""
        tool = self._tools.get(tool_id)
        return tool.circuit_threshold if tool else 5

    async def refresh(self) -> None:
        """从 Nacos 刷新工具配置（动态刷新，无需重启）"""
        await nacos_manager.refresh_config()
        all_tools = nacos_manager.get_all_tools()
        self._tools.clear()
        for tool_id, config_dict in all_tools.items():
            self._tools[tool_id] = ToolConfig(**config_dict)
        business_logger.info(f"工具注册中心刷新完成，共 {len(self._tools)} 个工具")


# 全局注册中心实例
tool_registry = ToolRegistry()
