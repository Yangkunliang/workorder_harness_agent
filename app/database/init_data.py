"""
自动生成模拟工单测试数据
- 启动时检查数据量，不足则插入
- 生成 20+ 条模拟工单
"""
import random
from datetime import datetime, timedelta

from sqlalchemy import select, func

from app.database.session import async_session
from app.database.models import Workorder


# 模拟数据模板
MOCK_TITLES = [
    "服务器CPU使用率异常告警",
    "数据库连接池耗尽问题",
    "线上支付接口超时",
    "用户登录失败排查",
    "消息队列积压处理",
    "缓存服务Redis集群故障",
    "API网关响应延迟优化",
    "日志采集服务异常",
    "定时任务执行失败",
    "文件上传服务不可用",
    "监控告警规则误报修复",
    "权限系统角色分配异常",
    "数据同步任务中断",
    "短信发送服务降级",
    "订单状态流转异常",
    "搜索服务索引重建",
    "配置中心热更新失败",
    "容器编排服务OOM",
    "微服务注册发现异常",
    "流量控制策略调整",
    "安全扫描漏洞修复",
    "CDN缓存刷新问题",
    "负载均衡策略优化",
    "灰度发布回滚处理",
]

MOCK_USERS = ["张三", "李四", "王五", "赵六", "钱七", "孙八", "周九", "吴十"]

MOCK_CONTENTS = [
    "发现线上服务出现异常，需要紧急排查处理。当前影响范围：全部用户，请尽快响应。",
    "系统监控告警触发，指标超过阈值，需要运维团队介入处理。当前告警级别：P1。",
    "业务方反馈功能不可用，经初步排查为后端服务异常，需要开发团队协助定位。",
    "日常巡检发现潜在风险，建议安排时间进行优化和修复，避免影响线上稳定性。",
    "客户投诉反馈问题，需要尽快确认原因并给出解决方案，同时更新工单状态。",
    "自动化测试发现回归问题，需要开发团队确认是否为已知问题并安排修复计划。",
]


async def init_mock_data() -> None:
    """初始化模拟数据：如果工单表为空则插入 25 条模拟数据"""
    async with async_session() as session:
        # 检查现有数据量
        result = await session.execute(select(func.count()).select_from(Workorder))
        count = result.scalar() or 0

        if count >= 20:
            print(f"[InitData] 工单表已有 {count} 条数据，跳过初始化")
            return

        # 生成模拟数据
        now = datetime.now()
        mock_workorders = []

        for i in range(25):
            days_ago = random.randint(0, 30)
            created_at = now - timedelta(days=days_ago, hours=random.randint(0, 23))
            workorder_no = f"WO{created_at.strftime('%Y%m%d')}{i + 1:04d}"
            title = MOCK_TITLES[i % len(MOCK_TITLES)]
            description = MOCK_CONTENTS[i % len(MOCK_CONTENTS)]
            creator = random.choice(MOCK_USERS)

            # 大部分为 pending 状态，少量 completed
            status = "completed" if i % 7 == 0 else "pending"

            wo = Workorder(
                workorder_no=workorder_no,
                title=title,
                description=description,
                creator=creator,
                status=status,
                created_at=created_at,
                updated_at=created_at,
                is_deleted=False,
            )
            mock_workorders.append(wo)

        session.add_all(mock_workorders)
        await session.commit()
        print(f"[InitData] 成功插入 {len(mock_workorders)} 条模拟工单数据")
