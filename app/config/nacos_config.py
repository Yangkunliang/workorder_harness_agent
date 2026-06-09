"""
Nacos 配置管理模块
- 从 .env 读取连接参数
- 连接 Nacos 拉取工具注册中心配置
- 支持动态刷新，内存缓存
"""
import json
import os
import logging
from typing import Any

import nacos
from dotenv import load_dotenv

load_dotenv()

# 配置日志
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


class NacosConfigManager:
    """Nacos 配置管理器，负责连接 Nacos 并管理工具注册中心配置"""

    def __init__(self) -> None:
        self.server_addresses: str = os.getenv("NACOS_SERVER_ADDRESSES", "127.0.0.1:8848")
        self.namespace: str = os.getenv("NACOS_NAMESPACE", "agent-harness")
        self.group: str = os.getenv("NACOS_GROUP", "DEFAULT_GROUP")
        self.username: str = os.getenv("NACOS_USERNAME", "nacos")
        self.password: str = os.getenv("NACOS_PASSWORD", "nacos")
        self.client: nacos.NacosClient | None = None
        self._tool_registry: dict[str, dict[str, Any]] = {}
        self._tool_config_raw: str = ""
        logger.info("[Nacos-Init] NacosConfigManager 初始化完成")
        logger.info(f"[Nacos-Init] 配置参数: server={self.server_addresses}, namespace={self.namespace}, group={self.group}")

    async def init(self) -> None:
        """初始化 Nacos 客户端并拉取工具配置"""
        logger.info("[Nacos-Init] 开始初始化 Nacos 客户端...")
        
        try:
            logger.info(f"[Nacos-Connect] 正在连接 Nacos: {self.server_addresses}")
            self.client = nacos.NacosClient(
                server_addresses=self.server_addresses,
                namespace=self.namespace,
                username=self.username,
                password=self.password,
            )
            logger.info("[Nacos-Connect] Nacos 客户端连接成功")

            # 尝试从 Nacos 拉取配置
            logger.info("[Nacos-Config] 开始拉取工具注册中心配置...")
            await self._pull_tool_config()

            # 如果 Nacos 中没有配置，则推送默认配置
            if not self._tool_registry:
                logger.warning("[Nacos-Config] Nacos 中未找到工具配置，准备推送默认配置")
                await self._push_default_tool_config()
                await self._pull_tool_config()

            # 添加配置变更监听（自动更新）
            self._add_config_listener()
            logger.info("[Nacos-Listener] 配置变更监听已启动")

            logger.info(f"[Nacos-Init] Nacos 初始化完成，共加载 {len(self._tool_registry)} 个工具")

        except Exception as e:
            logger.error(f"[Nacos-Error] 连接 Nacos 失败: {str(e)}")
            logger.warning("[Nacos-Fallback] 降级到本地默认工具配置")
            self._load_default_tool_config()

    def _add_config_listener(self) -> None:
        """添加 Nacos 配置变更监听，实现自动更新"""
        try:
            # 根据 nacos-sdk-python 版本选择正确的方法
            if hasattr(self.client, 'add_config_listener'):
                self.client.add_config_listener(
                    data_id="agent-tool-registry.json",
                    group=self.group,
                    cb=self._on_config_change
                )
            elif hasattr(self.client, 'add_listener'):
                self.client.add_listener(
                    data_id="agent-tool-registry.json",
                    group=self.group,
                    cb=self._on_config_change
                )
            else:
                # 如果都不支持，启动一个后台线程轮询
                import threading
                thread = threading.Thread(target=self._poll_config_changes, daemon=True)
                thread.start()
                logger.info(f"[Nacos-Listener] 使用轮询方式监听配置变更")
                return
            
            logger.info(f"[Nacos-Listener] 已注册配置监听: agent-tool-registry.json")
        except Exception as e:
            logger.error(f"[Nacos-Listener-Error] 注册监听失败: {str(e)}")
            # 降级到轮询方式
            import threading
            thread = threading.Thread(target=self._poll_config_changes, daemon=True)
            thread.start()
            logger.info(f"[Nacos-Listener] 降级到轮询方式监听配置变更")

    def _poll_config_changes(self) -> None:
        """轮询方式检测配置变更（降级方案）"""
        import time
        import asyncio
        last_md5 = ""
        while True:
            try:
                # 获取配置的 MD5 值来检测变更
                md5 = self.client.get_config_md5(
                    data_id="agent-tool-registry.json",
                    group=self.group
                )
                if md5 and md5 != last_md5:
                    last_md5 = md5
                    logger.info("[Nacos-Listener] 轮询检测到配置变更")
                    # 在新线程中执行异步操作
                    asyncio.run(self._pull_tool_config())
            except Exception as e:
                logger.debug(f"[Nacos-Listener-Poll] 轮询异常: {str(e)}")
            time.sleep(10)  # 每10秒轮询一次

    def _on_config_change(self, data_id: str, group: str, content: str) -> None:
        """配置变更回调函数，自动更新内存缓存"""
        logger.info(f"[Nacos-Listener] 检测到配置变更: data_id={data_id}, group={group}")
        try:
            if content:
                tools = json.loads(content)
                self._tool_registry = {tool["tool_id"]: tool for tool in tools}
                logger.info(f"[Nacos-Listener] 配置自动更新完成，当前共 {len(self._tool_registry)} 个工具")
                for tool_id in self._tool_registry.keys():
                    logger.debug(f"[Nacos-Listener] 工具: {tool_id}")
            else:
                logger.warning("[Nacos-Listener] 配置内容为空")
        except Exception as e:
            logger.error(f"[Nacos-Listener-Error] 配置解析失败: {str(e)}")

    async def _pull_tool_config(self) -> None:
        """从 Nacos 拉取工具注册中心配置"""
        try:
            logger.debug(f"[Nacos-Pull] 拉取配置: data_id=agent-tool-registry.json, group={self.group}")
            config_text = self.client.get_config(
                data_id="agent-tool-registry.json",
                group=self.group,
            )
            
            if config_text:
                self._tool_config_raw = config_text
                tools = json.loads(config_text)
                self._tool_registry = {tool["tool_id"]: tool for tool in tools}
                logger.info(f"[Nacos-Pull] 成功拉取 {len(self._tool_registry)} 个工具配置")
                for tool_id in self._tool_registry.keys():
                    logger.debug(f"[Nacos-Pull] 工具: {tool_id}")
            else:
                logger.warning("[Nacos-Pull] 拉取到空配置")

        except Exception as e:
            logger.error(f"[Nacos-Pull-Error] 拉取配置失败: {str(e)}")
            raise

    async def _push_default_tool_config(self) -> None:
        """向 Nacos 推送默认工具配置"""
        default_config = self._get_default_tool_config_json()
        try:
            logger.debug(f"[Nacos-Push] 推送默认配置到 Nacos")
            self.client.publish_config(
                data_id="agent-tool-registry.json",
                group=self.group,
                content=default_config,
                config_type="json",
            )
            logger.info("[Nacos-Push] 默认工具配置已成功推送到 Nacos")
        except Exception as e:
            logger.error(f"[Nacos-Push-Error] 推送默认配置失败: {str(e)}")
            raise

    def _load_default_tool_config(self) -> None:
        """加载本地默认工具配置（Nacos 不可用时的降级方案）"""
        tools = json.loads(self._get_default_tool_config_json())
        self._tool_registry = {tool["tool_id"]: tool for tool in tools}
        logger.info(f"[Nacos-Fallback] 已加载本地默认配置，共 {len(self._tool_registry)} 个工具")

    @staticmethod
    def _get_default_tool_config_json() -> str:
        """返回默认工具注册中心配置 JSON"""
        default_tools = [
            {
                "tool_id": "workorder_query",
                "tool_name": "查询工单",
                "request_schema": {
                    "type": "object",
                    "properties": {
                        "workorder_id": {"type": "string", "description": "工单编号"},
                        "create_user": {"type": "string", "description": "创建人"},
                        "status": {"type": "string", "description": "工单状态"}
                    }
                },
                "target_url": "/api/internal/workorder/query",
                "timeout": 5000,
                "max_retry": 2,
                "circuit_threshold": 5,
                "permission_tags": ["read"],
                "qps_limit": 50,
                "status": "active"
            },
            {
                "tool_id": "workorder_create",
                "tool_name": "新建工单",
                "request_schema": {
                    "type": "object",
                    "properties": {
                        "title": {"type": "string", "description": "工单标题"},
                        "content": {"type": "string", "description": "工单内容"},
                        "create_user": {"type": "string", "description": "创建人"}
                    },
                    "required": ["title", "content", "create_user"]
                },
                "target_url": "/api/internal/workorder/create",
                "timeout": 5000,
                "max_retry": 2,
                "circuit_threshold": 5,
                "permission_tags": ["write"],
                "qps_limit": 20,
                "status": "active"
            },
            {
                "tool_id": "workorder_urge",
                "tool_name": "工单催办",
                "request_schema": {
                    "type": "object",
                    "properties": {
                        "workorder_id": {"type": "string", "description": "工单编号"}
                    },
                    "required": ["workorder_id"]
                },
                "target_url": "/api/internal/workorder/urge",
                "timeout": 5000,
                "max_retry": 2,
                "circuit_threshold": 5,
                "permission_tags": ["write"],
                "qps_limit": 10,
                "status": "active"
            },
            {
                "tool_id": "workorder_close",
                "tool_name": "关闭工单",
                "request_schema": {
                    "type": "object",
                    "properties": {
                        "workorder_id": {"type": "string", "description": "工单编号"}
                    },
                    "required": ["workorder_id"]
                },
                "target_url": "/api/internal/workorder/close",
                "timeout": 5000,
                "max_retry": 0,
                "circuit_threshold": 3,
                "permission_tags": ["write", "risk"],
                "qps_limit": 5,
                "status": "active"
            },
            {
                "tool_id": "workorder_delete",
                "tool_name": "删除工单",
                "request_schema": {
                    "type": "object",
                    "properties": {
                        "workorder_id": {"type": "string", "description": "工单编号"}
                    },
                    "required": ["workorder_id"]
                },
                "target_url": "/api/internal/workorder/delete",
                "timeout": 5000,
                "max_retry": 0,
                "circuit_threshold": 3,
                "permission_tags": ["write", "risk"],
                "qps_limit": 5,
                "status": "active"
            }
        ]
        return json.dumps(default_tools, ensure_ascii=False, indent=2)

    def get_tool_config(self, tool_id: str) -> dict[str, Any] | None:
        """根据 tool_id 获取工具配置"""
        config = self._tool_registry.get(tool_id)
        if config:
            logger.debug(f"[Nacos-Get] 获取工具配置成功: {tool_id}")
        else:
            logger.warning(f"[Nacos-Get] 未找到工具配置: {tool_id}")
        return config

    def get_all_tools(self) -> dict[str, dict[str, Any]]:
        """获取所有工具配置"""
        return self._tool_registry.copy()

    async def refresh_config(self) -> None:
        """手动刷新 Nacos 配置（支持动态刷新，无需重启）"""
        logger.info("[Nacos-Refresh] 手动触发配置刷新")
        await self._pull_tool_config()
        logger.info(f"[Nacos-Refresh] 配置刷新完成，当前 {len(self._tool_registry)} 个工具")

    async def close(self) -> None:
        """关闭 Nacos 客户端"""
        self.client = None
        logger.info("[Nacos-Close] Nacos 客户端已关闭")


# 全局单例
nacos_manager = NacosConfigManager()