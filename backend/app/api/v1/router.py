"""API 路由汇总"""

from fastapi import APIRouter

from app.api.v1.endpoints import health, insight, topic, workflow

api_router = APIRouter()

# 健康检查
api_router.include_router(health.router, prefix="/health", tags=["Health"])

# 洞见 API
api_router.include_router(insight.router, prefix="/insights", tags=["Insights"])

# 主题管理 API
api_router.include_router(topic.router, prefix="/topics", tags=["Topics"])

# 工作流 API
api_router.include_router(workflow.router, tags=["Workflow"])
