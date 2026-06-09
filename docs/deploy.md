# 本地部署 & 启动 & 测试步骤

## 一、环境准备

### 1.1 安装 Docker Desktop
确保本地已安装 Docker Desktop 并启动。

### 1.2 启动基础设施（MySQL、Redis、Nacos）

```bash
# 启动 MySQL 8.0
docker run -d \
  --name mysql8 \
  -p 3306:3306 \
  -e MYSQL_ROOT_PASSWORD=root123 \
  -e MYSQL_DATABASE=agent_workorder \
  mysql:8.0 \
  --character-set-server=utf8mb4 \
  --collation-server=utf8mb4_unicode_ci

# 启动 Redis
docker run -d \
  --name redis \
  -p 6379:6379 \
  redis:7-alpine

# 启动 Nacos
docker run -d \
  --name nacos \
  -e MODE=standalone \
  -p 8848:8848 \
  -p 9848:9848 \
  nacos/nacos-server:v2.3.2
```

### 1.3 验证基础设施

```bash
# 验证 MySQL
docker exec -it mysql8 mysql -uroot -proot123 -e "SHOW DATABASES;"

# 验证 Redis
docker exec -it redis redis-cli ping

# 验证 Nacos（浏览器访问）
# http://localhost:8848/nacos  账号/密码：nacos/nacos
```

## 二、项目部署

### 2.1 安装 Python 依赖

推荐使用 uv 包管理器（更快更可靠）：

```bash
cd workorder_harness_agent

# 使用 uv 安装依赖
uv pip install -r requirements.txt

# 或者使用传统 pip（需先激活虚拟环境）
# source venv/bin/activate
# pip install -r requirements.txt
```

### 2.2 配置环境变量

编辑 `.env` 文件，确认以下配置正确：

```env
# MySQL
MYSQL_HOST=127.0.0.1
MYSQL_PORT=3307
MYSQL_USER=root
MYSQL_PASSWORD=root123
MYSQL_DATABASE=agent_workorder

# Redis
REDIS_HOST=127.0.0.1
REDIS_PORT=6379

# Nacos
NACOS_SERVER_ADDRESSES=127.0.0.1:8848
NACOS_NAMESPACE=agent-harness
NACOS_GROUP=DEFAULT_GROUP

# 阿里云百炼平台 LLM 配置（替换为你的 API Key）
LLM_API_KEY=your-dashscope-api-key
LLM_API_BASE=https://dashscope.aliyuncs.com/compatible-mode/v1
LLM_MODEL=qwen-plus

# 服务配置
SERVER_PORT=8090
```

### 2.3 配置 Nacos 命名空间

1. 登录 Nacos 控制台：http://localhost:8848/nacos
2. 进入「命名空间」管理页面
3. 新建命名空间：`agent-harness`
4. 项目启动时会自动推送工具注册中心配置到 Nacos

## 三、启动服务

```bash
python main.py
```

启动成功后会看到：
```
[Startup] 正在初始化数据库...
[Startup] 数据库初始化完成
[Startup] 正在连接 Nacos 并拉取工具配置...
[Startup] Nacos 工具配置加载完成
[Startup] 服务启动完成，端口: 8090
```

## 四、接口测试

### 4.1 健康检查

```bash
curl http://localhost:8090/health
```

预期返回：
```json
{"status": "healthy", "service": "workorder-harness-agent"}
```

### 4.2 查询工单

```bash
curl -X POST http://localhost:8090/api/chat \
  -H "Content-Type: application/json" \
  -d '{
    "session_id": "test-001",
    "user_id": "user001",
    "message": "查询张三的工单",
    "ip_address": "127.0.0.1"
  }'
```

### 4.3 新建工单

```bash
curl -X POST http://localhost:8090/api/chat \
  -H "Content-Type: application/json" \
  -d '{
    "session_id": "test-002",
    "user_id": "user001",
    "message": "创建工单，标题：服务器告警，内容：CPU使用率超过90%，创建人：张三",
    "ip_address": "127.0.0.1"
  }'
```

### 4.4 工单催办

```bash
curl -X POST http://localhost:8090/api/chat \
  -H "Content-Type: application/json" \
  -d '{
    "session_id": "test-003",
    "user_id": "user001",
    "message": "催办工单 WO202606090001",
    "ip_address": "127.0.0.1"
  }'
```

### 4.5 关闭工单（高危操作 - 需二次确认）

**第一步：请求关闭**
```bash
curl -X POST http://localhost:8090/api/chat \
  -H "Content-Type: application/json" \
  -d '{
    "session_id": "test-004",
    "user_id": "user001",
    "message": "关闭工单 WO202606090001",
    "ip_address": "127.0.0.1"
  }'
```

预期返回确认话术，提示用户回复「确认执行」或「取消」。

**第二步：确认执行**
```bash
curl -X POST http://localhost:8090/api/chat \
  -H "Content-Type: application/json" \
  -d '{
    "session_id": "test-004",
    "user_id": "user001",
    "message": "确认执行",
    "ip_address": "127.0.0.1"
  }'
```

### 4.6 删除工单（高危操作 - 需二次确认）

流程同关闭工单，将「关闭」替换为「删除」。

## 五、验证数据

### 5.1 查看工单数据

```bash
docker exec -it mysql8 mysql -uroot -proot123 agent_workorder \
  -e "SELECT workorder_id, title, status, create_user FROM workorder LIMIT 10;"
```

### 5.2 查看审计日志

```bash
docker exec -it mysql8 mysql -uroot -proot123 agent_workorder \
  -e "SELECT * FROM operation_audit_log ORDER BY create_time DESC LIMIT 10;"
```

### 5.3 查看 Nacos 工具配置

浏览器访问：http://localhost:8848/nacos
进入「配置管理」→ 命名空间 `agent-harness` → `agent-tool-registry.json`

## 六、单元测试

```bash
cd workorder_harness_agent
python -m pytest tests/ -v
```
