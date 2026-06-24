"""Project Insight FastAPI 应用入口

基于多智能体协同的深度洞见精炼引擎。
"""

from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.openapi.docs import get_swagger_ui_html, get_redoc_html
from fastapi.responses import HTMLResponse

from app.api.v1.router import api_router
from app.config import settings

# Xiaomi MiMo 极简美学 CSS
MIMO_CUSTOM_CSS = """
<style>
    /* Xiaomi MiMo Explore and Love - 极简美学 */

    /* 全局背景：高级米白色 */
    .swagger-ui {
        background-color: #F9F9F6 !important;
    }

    .swagger-ui .wrapper {
        background-color: #F9F9F6 !important;
    }

    /* 隐藏顶部难看的绿色 Header */
    .swagger-ui .topbar {
        display: none !important;
    }

    /* 全局主字体颜色：深灰色 */
    .swagger-ui,
    .swagger-ui .opblock-tag,
    .swagger-ui .opblock-tag-section h3,
    .swagger-ui .opblock .opblock-summary-operation-id,
    .swagger-ui .opblock .opblock-summary-path,
    .swagger-ui .opblock .opblock-summary-description,
    .swagger-ui table thead tr th,
    .swagger-ui .response-col_status,
    .swagger-ui .response-col_description,
    .swagger-ui .parameter__name,
    .swagger-ui .parameter__type,
    .swagger-ui .parameter__deprecated,
    .swagger-ui .parameter__in,
    .swagger-ui .model-title,
    .swagger-ui .model {
        color: #333333 !important;
    }

    /* 标题样式优化 */
    .swagger-ui .title {
        color: #2C2C2C !important;
        font-weight: 600 !important;
    }

    /* API 模块扁平化：去掉边框和阴影 */
    .swagger-ui .opblock {
        border: none !important;
        box-shadow: none !important;
        border-radius: 8px !important;
        margin-bottom: 8px !important;
        background: rgba(255, 255, 255, 0.8) !important;
    }

    .swagger-ui .opblock .opblock-summary {
        border: none !important;
    }

    .swagger-ui .opblock-body {
        border: none !important;
    }

    /* API 方法标签极简化 */
    .swagger-ui .opblock .opblock-summary-method {
        border-radius: 6px !important;
        font-size: 12px !important;
        font-weight: 600 !important;
        padding: 4px 10px !important;
        min-width: 60px !important;
        text-align: center !important;
    }

    /* GET 方法：柔和蓝 */
    .swagger-ui .opblock.opblock-get .opblock-summary-method {
        background: #E8F4FD !important;
        color: #1A73E8 !important;
    }

    /* POST 方法：柔和绿 */
    .swagger-ui .opblock.opblock-post .opblock-summary-method {
        background: #E6F4EA !important;
        color: #1E8E3E !important;
    }

    /* PUT 方法：柔和橙 */
    .swagger-ui .opblock.opblock-put .opblock-summary-method {
        background: #FEF7E0 !important;
        color: #E37400 !important;
    }

    /* DELETE 方法：柔和红 */
    .swagger-ui .opblock.opblock-delete .opblock-summary-method {
        background: #FCE8E6 !important;
        color: #D93025 !important;
    }

    /* 模型区块优化 */
    .swagger-ui section.models {
        border: none !important;
        background: rgba(255, 255, 255, 0.8) !important;
        border-radius: 8px !important;
        padding: 16px !important;
    }

    .swagger-ui section.models h4 {
        color: #2C2C2C !important;
        border-bottom: 1px solid #E0E0E0 !important;
    }

    /* 输入框优化 */
    .swagger-ui input[type=text],
    .swagger-ui textarea {
        background: #FFFFFF !important;
        border: 1px solid #E0E0E0 !important;
        border-radius: 6px !important;
        color: #333333 !important;
    }

    .swagger-ui input[type=text]:focus,
    .swagger-ui textarea:focus {
        border-color: #1A73E8 !important;
        box-shadow: 0 0 0 2px rgba(26, 115, 232, 0.1) !important;
    }

    /* 按钮极简化 */
    .swagger-ui .btn {
        border-radius: 6px !important;
        font-weight: 500 !important;
        box-shadow: none !important;
    }

    .swagger-ui .btn.execute {
        background: #1A73E8 !important;
        color: #FFFFFF !important;
        border: none !important;
    }

    .swagger-ui .btn.execute:hover {
        background: #1557B0 !important;
    }

    /* 响应状态码优化 */
    .swagger-ui .response-col_status {
        font-weight: 600 !important;
    }

    /* 服务器选择器优化 */
    .swagger-ui .scheme-container {
        background: rgba(255, 255, 255, 0.8) !important;
        border: none !important;
        box-shadow: none !important;
        border-radius: 8px !important;
    }

    /* 滚动条美化 */
    .swagger-ui ::-webkit-scrollbar {
        width: 6px;
        height: 6px;
    }

    .swagger-ui ::-webkit-scrollbar-track {
        background: transparent;
    }

    .swagger-ui ::-webkit-scrollbar-thumb {
        background: #C0C0C0;
        border-radius: 3px;
    }

    .swagger-ui ::-webkit-scrollbar-thumb:hover {
        background: #A0A0A0;
    }

    /* 描述区域优化 */
    .swagger-ui .info {
        margin: 30px 0 !important;
    }

    .swagger-ui .info .title {
        font-size: 28px !important;
        color: #1A1A1A !important;
        font-weight: 700 !important;
    }

    .swagger-ui .info .description p {
        color: #666666 !important;
        font-size: 14px !important;
        line-height: 1.6 !important;
    }

    /* MiMo 品牌标识 */
    .swagger-ui .info .description::before {
        content: "Xiaomi MiMo · Explore and Love";
        display: block;
        font-size: 12px;
        color: #FF6900 !important;
        font-weight: 600;
        letter-spacing: 1px;
        margin-bottom: 12px;
        text-transform: uppercase;
    }
</style>
"""


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """应用生命周期管理

    startup: 初始化数据库连接、启动定时调度器
    shutdown: 清理资源
    """
    # Startup
    print(f"[STARTUP] Project Insight starting in {settings.APP_ENV} mode...")
    print(f"[STARTUP] LLM Model: {settings.LLM_MODEL}")
    print(f"[STARTUP] Daily Budget: ${settings.DAILY_BUDGET_USD}")

    # 启动定时调度器
    from app.services.scheduler import start_scheduler
    scheduler = start_scheduler()

    yield

    # Shutdown
    if scheduler:
        scheduler.shutdown()
    print("[SHUTDOWN] Project Insight shutting down...")


def create_app() -> FastAPI:
    """创建 FastAPI 应用实例"""

    app = FastAPI(
        title="Project Insight API",
        description=(
            "基于多智能体协同的深度洞见精炼引擎\n\n"
            "A multi-agent powered insight refinement engine that transforms "
            "raw information into actionable wisdom."
        ),
        version="0.1.0",
        docs_url=None,  # 禁用默认 docs
        redoc_url=None,  # 禁用默认 redoc
        lifespan=lifespan,
    )

    # 配置 CORS
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.CORS_ORIGINS,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # 注册 API 路由
    app.include_router(api_router, prefix="/api/v1")

    # 自定义 Swagger UI 路由 - Xiaomi MiMo 极简美学
    @app.get("/docs", include_in_schema=False)
    async def custom_swagger_ui(request: Request):
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>{app.title} - Explore and Love</title>
            <link rel="icon" href="https://fastapi.tiangolo.com/img/favicon.png"/>
            <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/swagger-ui-dist@5/swagger-ui.css"/>
            {MIMO_CUSTOM_CSS}
        </head>
        <body>
            <div id="swagger-ui"></div>
            <script src="https://cdn.jsdelivr.net/npm/swagger-ui-dist@5/swagger-ui-bundle.js"></script>
            <script>
                SwaggerUIBundle({{
                    url: '{app.openapi_url}',
                    dom_id: '#swagger-ui',
                    presets: [
                        SwaggerUIBundle.presets.apis,
                        SwaggerUIBundle.SwaggerUIStandalonePreset
                    ],
                    layout: "BaseLayout"
                }});
            </script>
        </body>
        </html>
        """
        return HTMLResponse(content=html_content)

    # 自定义 ReDoc 路由
    @app.get("/redoc", include_in_schema=False)
    async def custom_redoc(request: Request):
        return get_redoc_html(
            openapi_url=app.openapi_url,
            title=f"{app.title} - API Reference",
            redoc_js_url="https://cdn.jsdelivr.net/npm/redoc@next/bundles/redoc.standalone.js",
            redoc_favicon_url="https://fastapi.tiangolo.com/img/favicon.png",
            with_google_fonts=False,
        )

    return app


# 创建应用实例
app = create_app()


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.DEBUG,
    )
