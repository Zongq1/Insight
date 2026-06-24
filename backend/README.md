# Project Insight Backend

基于多智能体协同的深度洞见精炼引擎 - 后端服务

## 技术栈

- **Python 3.11+**
- **FastAPI** - 异步 Web 框架
- **LangGraph** - 多智能体编排
- **Instructor** - LLM 结构化输出
- **Pydantic V2** - 数据验证
- **SQLAlchemy 2.0** - 异步 ORM
- **PostgreSQL** - 关系型数据库
- **Redis** - 缓存和消息队列
- **ChromaDB** - 向量数据库
- **Celery** - 异步任务队列

## 快速开始

### 1. 安装依赖

```bash
# 安装 Poetry
pip install poetry

# 安装项目依赖
poetry install

# 激活虚拟环境
poetry shell
```

### 2. 配置环境变量

```bash
# 复制环境变量示例文件
cp .env.example .env

# 编辑 .env 文件，填入实际配置
# 至少需要配置 OPENAI_API_KEY
```

### 3. 启动数据库

```bash
# 使用 Docker 启动 PostgreSQL
docker run -d \
  --name insight-postgres \
  -e POSTGRES_USER=insight \
  -e POSTGRES_PASSWORD=insight123 \
  -e POSTGRES_DB=insight \
  -p 5432:5432 \
  postgres:16-alpine

# 使用 Docker 启动 Redis
docker run -d \
  --name insight-redis \
  -p 6379:6379 \
  redis:7-alpine
```

### 4. 运行数据库迁移

```bash
alembic upgrade head
```

### 5. 启动服务

```bash
# 开发模式
uvicorn app.main:app --reload

# 访问 API 文档
# http://localhost:8000/docs
```

## 开发

### 运行测试

```bash
# 运行所有测试
pytest

# 运行特定测试
pytest tests/unit/test_models/

# 运行带覆盖率的测试
pytest --cov=app --cov-report=html
```

### 代码质量检查

```bash
# Ruff 检查
ruff check .

# MyPy 类型检查
mypy app/

# Black 格式化
black app/ tests/

# isort 导入排序
isort app/ tests/
```

## 项目结构

```
backend/
├── app/
│   ├── main.py              # FastAPI 应用入口
│   ├── config.py            # 配置管理
│   ├── core/                # 核心模块
│   ├── api/                 # API 端点
│   ├── models/              # 数据模型
│   ├── services/            # 业务服务
│   ├── repositories/        # 数据访问层
│   └── utils/               # 工具函数
├── tests/                   # 测试代码
├── scripts/                 # 脚本工具
├── pyproject.toml           # 项目配置
└── alembic/                 # 数据库迁移
```

## API 文档

启动服务后访问：
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc
