"""洞见 API 端点"""

import logging
from datetime import date
from typing import Optional

from fastapi import APIRouter, BackgroundTasks, HTTPException, Query
from pydantic import BaseModel

logger = logging.getLogger(__name__)

router = APIRouter()


class InsightResponse(BaseModel):
    """洞见响应模型"""

    id: str
    category: str
    core_thesis: str
    logic_chain: list[dict]
    historical_insight: Optional[str]
    sources: list[dict]
    confidence_score: float
    date_generated: str


class InsightListResponse(BaseModel):
    """洞见列表响应模型"""

    items: list[InsightResponse]
    total: int
    page: int
    page_size: int


# 中文 fallback 测试数据
_FALLBACK_INSIGHTS = [
    InsightResponse(
        id="insight-001",
        category="AI与科技",
        core_thesis="大语言模型正从纯规模扩展转向架构效率提升，混合专家模型和稀疏注意力成为新前沿。",
        logic_chain=[
            {"premise": "密集模型训练成本超过1亿美元", "conclusion": "MoE架构可减少60-80%计算量"},
            {"premise": "稀疏注意力提升上下文长度", "conclusion": "百万级token窗口成为可能"},
        ],
        historical_insight="类似于1990年代RISC架构在特定工作负载上取代CISC的历史进程。",
        sources=[
            {"name": "Anthropic 研究博客", "url": "https://research.anthropic.com"},
            {"name": "Google DeepMind", "url": "https://deepmind.google"},
        ],
        confidence_score=0.87,
        date_generated=str(date.today()),
    ),
    InsightResponse(
        id="insight-002",
        category="地缘政治",
        core_thesis="供应链多元化正在加速，各国优先考虑韧性而非效率，重塑全球贸易格局。",
        logic_chain=[
            {"premise": "疫情暴露了单点故障风险", "conclusion": "近岸投资自2022年增长了三倍"},
            {"premise": "美国、欧盟、日本推出半导体补贴", "conclusion": "芯片生产地理分布趋于分散"},
        ],
        historical_insight="呼应1930年代从英国自由贸易向保护主义集团的转变。",
        sources=[
            {"name": "金融时报", "url": "https://ft.com"},
            {"name": "布鲁金斯学会", "url": "https://brookings.edu"},
        ],
        confidence_score=0.72,
        date_generated=str(date.today()),
    ),
    InsightResponse(
        id="insight-003",
        category="金融",
        core_thesis="央行数字货币正从试点走向量产，130多个国家正在探索CBDC，11个已正式发行。",
        logic_chain=[
            {"premise": "发达经济体现金使用量持续下降", "conclusion": "数字法币成为基础设施必需品"},
            {"premise": "中国数字人民币钱包达2.6亿", "conclusion": "在可编程货币领域获得先发优势"},
        ],
        historical_insight="类似于1970年代从金本位向法定货币的转型。",
        sources=[
            {"name": "国际清算银行", "url": "https://bis.org"},
            {"name": "IMF博客", "url": "https://imf.org/blog"},
        ],
        confidence_score=0.65,
        date_generated=str(date.today()),
    ),
]


async def _query_insights_from_db(
    target_date: Optional[date] = None,
    page: int = 1,
    page_size: int = 50,
) -> tuple[list[InsightResponse], int]:
    """从数据库查询洞见

    Args:
        target_date: 指定日期（None 则查全部）
        page: 页码
        page_size: 每页数量

    Returns:
        (insights 列表, 总数)
    """
    try:
        from sqlalchemy import func, select
        from app.models.db.base import get_session_factory
        from app.models.db.insight import Insight as InsightORM

        session_factory = get_session_factory()
        async with session_factory() as session:
            # 构建查询
            base_query = select(InsightORM)
            count_query = select(func.count(InsightORM.id))

            if target_date:
                base_query = base_query.where(InsightORM.date_generated == target_date)
                count_query = count_query.where(InsightORM.date_generated == target_date)

            # 总数
            total_result = await session.execute(count_query)
            total = total_result.scalar() or 0

            # 分页查询
            offset = (page - 1) * page_size
            stmt = base_query.order_by(InsightORM.id.desc()).offset(offset).limit(page_size)
            result = await session.execute(stmt)
            rows = result.scalars().all()

            if not rows:
                return [], total

            insights = []
            for row in rows:
                insights.append(InsightResponse(
                    id=str(row.id),
                    category=row.category,
                    core_thesis=row.core_thesis,
                    logic_chain=row.logic_chain or [],
                    historical_insight=row.historical_insight,
                    sources=row.sources or [],
                    confidence_score=row.confidence_score,
                    date_generated=str(row.date_generated),
                ))
            return insights, total
    except Exception as e:
        logger.warning(f"DB query failed, using fallback: {e}")
        return [], 0


@router.get("", response_model=list[InsightResponse])
async def get_all_insights() -> list[InsightResponse]:
    """获取所有洞见

    优先从数据库查询，无数据时返回中文 fallback 测试数据。
    """
    insights, _ = await _query_insights_from_db()
    if insights:
        return insights
    return _FALLBACK_INSIGHTS


@router.get("/today", response_model=InsightListResponse)
async def get_today_insights(
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(10, ge=1, le=50, description="每页数量"),
) -> InsightListResponse:
    """获取今日洞见

    返回当天生成的洞见卡片列表。
    """
    insights, total = await _query_insights_from_db(
        target_date=date.today(),
        page=page,
        page_size=page_size,
    )

    return InsightListResponse(
        items=insights,
        total=total,
        page=page,
        page_size=page_size,
    )


@router.post("/refresh")
async def refresh_insights(background_tasks: BackgroundTasks):
    """手动触发 Workflow 刷新

    立即返回，后台执行 Workflow 并将结果写入数据库。
    """
    import uuid

    thread_id = str(uuid.uuid4())[:8]

    async def _run_refresh():
        from app.services.scheduler import run_scheduled_workflow
        await run_scheduled_workflow()

    background_tasks.add_task(_run_refresh)

    return {"message": "Workflow 已在后台启动", "thread_id": thread_id}


@router.get("/{insight_id}", response_model=InsightResponse)
async def get_insight(insight_id: str) -> InsightResponse:
    """获取单个洞见详情

    根据 ID 获取洞见的完整信息。
    """
    try:
        from sqlalchemy import select
        from app.models.db.base import get_session_factory
        from app.models.db.insight import Insight as InsightORM

        session_factory = get_session_factory()
        async with session_factory() as session:
            stmt = select(InsightORM).where(InsightORM.id == int(insight_id))
            result = await session.execute(stmt)
            row = result.scalar_one_or_none()

            if not row:
                raise HTTPException(status_code=404, detail="Insight not found")

            return InsightResponse(
                id=str(row.id),
                category=row.category,
                core_thesis=row.core_thesis,
                logic_chain=row.logic_chain or [],
                historical_insight=row.historical_insight,
                sources=row.sources or [],
                confidence_score=row.confidence_score,
                date_generated=str(row.date_generated),
            )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get insight {insight_id}: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/category/{category}", response_model=InsightListResponse)
async def get_insights_by_category(
    category: str,
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(10, ge=1, le=50, description="每页数量"),
) -> InsightListResponse:
    """按分类获取洞见

    返回指定分类的洞见列表。
    """
    try:
        from sqlalchemy import func, select
        from app.models.db.base import get_session_factory
        from app.models.db.insight import Insight as InsightORM

        session_factory = get_session_factory()
        async with session_factory() as session:
            # 总数
            count_stmt = select(func.count(InsightORM.id)).where(InsightORM.category == category)
            total_result = await session.execute(count_stmt)
            total = total_result.scalar() or 0

            # 分页查询
            offset = (page - 1) * page_size
            stmt = (
                select(InsightORM)
                .where(InsightORM.category == category)
                .order_by(InsightORM.id.desc())
                .offset(offset)
                .limit(page_size)
            )
            result = await session.execute(stmt)
            rows = result.scalars().all()

            insights = [
                InsightResponse(
                    id=str(row.id),
                    category=row.category,
                    core_thesis=row.core_thesis,
                    logic_chain=row.logic_chain or [],
                    historical_insight=row.historical_insight,
                    sources=row.sources or [],
                    confidence_score=row.confidence_score,
                    date_generated=str(row.date_generated),
                )
                for row in rows
            ]

            return InsightListResponse(
                items=insights,
                total=total,
                page=page,
                page_size=page_size,
            )
    except Exception as e:
        logger.error(f"Failed to query by category: {e}")
        return InsightListResponse(items=[], total=0, page=page, page_size=page_size)
