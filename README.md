# 绣花机智能工厂后端 MVP

这是一个从零搭建的绣花机智能工厂后端 MVP。第一版不接真实硬件，设备通过 HTTP 上传模拟数据；后续可以在 `services` 层旁边新增 MQTT 消费者，把 MQTT 消息转换为同一套 `MachineStatusUpload` 数据结构后复用入库逻辑。

## 技术栈

- 后端：Python + FastAPI
- 数据库：PostgreSQL
- ORM：SQLAlchemy 2.x
- 数据迁移：Alembic
- API 文档：FastAPI Swagger / OpenAPI
- 本地编排：Docker Compose
- 设备接入：HTTP 上传（预留 MQTT 扩展）

## 项目结构

```text
app/
  main.py                  # FastAPI 入口
  config.py                # 环境变量配置
  database.py              # SQLAlchemy engine/session/Base
  models/                  # SQLAlchemy 数据模型
  schemas/                 # Pydantic 请求/响应模型
  routers/                 # API 路由
  services/                # 业务逻辑与入库逻辑
alembic/
  env.py                   # Alembic 配置
  versions/                # 数据库迁移脚本
scripts/
  simulate_machine.py      # 模拟绣花机上传脚本
Dockerfile
docker-compose.yml
requirements.txt
README.md
```

## 已实现模型

- `User`：用户基础信息，预留 APP 登录/权限使用。
- `Factory`：工厂信息。
- `Machine`：机器基础信息，包含 `machine_id` 和最后上传时间 `last_seen_at`。
- `MachineStatus`：每次设备状态上传的原始状态记录。
- `AlarmRecord`：当上传数据包含 `alarm_code` 时生成报警记录。
- `ProductionRecord`：按上传快照保存生产数据，当前统计接口按当天最大累计值计算。

## 安装

### 方式一：Docker Compose（推荐）

确保已经安装 Docker 和 Docker Compose，然后在项目根目录执行：

```bash
docker compose up --build
```

该命令会启动：

- PostgreSQL：`localhost:5432`
- FastAPI：`http://localhost:8000`

API 容器启动时会自动执行：

```bash
alembic upgrade head
```

所以正常情况下无需手动初始化数据库。

### 方式二：本地 Python 环境

需要本地已有 PostgreSQL，并创建数据库：

```bash
createdb embroidery_factory
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
export DATABASE_URL="postgresql+psycopg://postgres:postgres@localhost:5432/embroidery_factory"
alembic upgrade head
uvicorn app.main:app --reload
```

## 初始化数据库

如果使用 Docker Compose，数据库迁移会在 API 容器启动时自动执行。

如果需要手动执行迁移：

```bash
docker compose exec api alembic upgrade head
```

或本地执行：

```bash
alembic upgrade head
```

## 运行模拟机器

先启动后端：

```bash
docker compose up --build
```

然后在另一个终端执行：

```bash
python scripts/simulate_machine.py --machine-id CBL001
```

脚本默认每 5 秒向以下接口上传一次随机状态：

```text
POST http://localhost:8000/api/machine/status
```

也可以指定 URL 和上传间隔：

```bash
python scripts/simulate_machine.py \
  --url http://localhost:8000/api/machine/status \
  --machine-id CBL002 \
  --interval 5
```

## Swagger 文档

启动后访问：

- Swagger UI：<http://localhost:8000/docs>
- ReDoc：<http://localhost:8000/redoc>
- OpenAPI JSON：<http://localhost:8000/openapi.json>

## 核心 API

### 健康检查

```http
GET /health
```

### 机器状态上传

```http
POST /api/machine/status
```

示例请求：

```json
{
  "machine_id": "CBL001",
  "status": "running",
  "rpm": 1500,
  "current_stitches": 58200,
  "finished_pieces": 36,
  "work_hours": 7.5,
  "alarm_code": null,
  "pattern_id": "P001",
  "timestamp": "2026-05-14T10:30:00Z"
}
```

### APP 查询接口

```http
GET /api/machines
GET /api/machines/{machine_id}/status
GET /api/machines/{machine_id}/stats?date=YYYY-MM-DD
GET /api/factories/{factory_id}/machines
```

另外提供一个便于开发初始化机器的接口：

```http
POST /api/machines
```

## 在线状态判断

后端以服务器收到上传的时间 `last_seen_at` 判断在线状态：

- 最近 15 秒内有上传：`online`
- 超过 15 秒没有上传：`offline`

阈值可以通过环境变量调整：

```bash
OFFLINE_THRESHOLD_SECONDS=15
```

## 快速验证

启动服务后执行一次手工上传：

```bash
curl -X POST http://localhost:8000/api/machine/status \
  -H 'Content-Type: application/json' \
  -d '{
    "machine_id": "CBL001",
    "status": "running",
    "rpm": 1500,
    "current_stitches": 58200,
    "finished_pieces": 36,
    "work_hours": 7.5,
    "alarm_code": null,
    "pattern_id": "P001",
    "timestamp": "2026-05-14T10:30:00Z"
  }'
```

查询机器列表：

```bash
curl http://localhost:8000/api/machines
```

查询机器当天统计：

```bash
curl 'http://localhost:8000/api/machines/CBL001/stats?date=2026-05-14'
```

## 后续扩展建议

- 增加用户认证：JWT 登录、工厂/角色权限控制。
- 增加 MQTT 接入：新增 MQTT consumer，把消息解析为 `MachineStatusUpload` 后复用 `record_status`。
- 增加真实生产班次统计：按班次、订单、花样、机器维度聚合。
- 增加报警恢复闭环：报警开始、确认、恢复时间、处理人。
- 增加时序数据清理和归档策略。
