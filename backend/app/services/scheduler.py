"""定时调度器

使用 APScheduler 定时执行 Workflow，将结果写入数据库。
Android 端只读数据库，毫秒级响应。
"""

import logging
from datetime import date, datetime

from app.config import settings

logger = logging.getLogger(__name__)


async def run_scheduled_workflow():
    """定时执行 Workflow

    1. 从 NewsNow 抓取多平台热点
    2. 将热点标题作为 raw_texts 输入 LangGraph Workflow
    3. 将 final_briefings 保存到 insights 表
    """
    from app.services.agents.newsnow_client import newsnow_client
    from app.services.agents.workflow import InsightWorkflow

    logger.info("[Scheduler] Starting scheduled workflow...")

    try:
        # 1. 抓取 NewsNow 热点
        platforms = [p.strip() for p in settings.NEWSNOW_PLATFORMS.split(",") if p.strip()]
        articles = await newsnow_client.fetch_multiple(platforms=platforms)

        if not articles:
            logger.warning("[Scheduler] NewsNow returned 0 articles, skipping workflow")
            return

        # 2. 按平台聚合热点为较长文本（单个标题太短，Distiller 无法处理）
        from collections import defaultdict
        platform_groups: dict[str, list[str]] = defaultdict(list)
        for a in articles[:30]:
            platform_groups[a.source].append(a.title)

        raw_texts = []
        for platform, titles in platform_groups.items():
            combined = f"【{platform}热点】\n" + "\n".join(f"• {t}" for t in titles[:10])
            raw_texts.append(combined)
        logger.info(f"[Scheduler] Got {len(articles)} topics, grouped into {len(raw_texts)} text blocks")

        # 3. 执行 Workflow
        workflow = InsightWorkflow()
        result = await workflow.run(
            topic="综合热点",
            raw_texts=raw_texts,
        )

        # 4. 保存到数据库
        final_briefings = result.get("final_briefings", [])
        if final_briefings:
            await _save_briefings_to_db(final_briefings)
            logger.info(f"[Scheduler] Saved {len(final_briefings)} insights to DB")
        else:
            logger.warning("[Scheduler] Workflow produced 0 insights")

        # 5. 清理旧数据
        await _cleanup_old_insights(days=7)

    except Exception as e:
        logger.error(f"[Scheduler] Workflow failed: {e}")


async def _save_briefings_to_db(briefings: list):
    """将 Workflow 结果保存到数据库"""
    try:
        from app.models.db.base import get_session_factory
        from app.models.db.insight import Insight

        session_factory = get_session_factory()
        async with session_factory() as session:
            for b in briefings:
                b_dict = b.model_dump() if hasattr(b, "model_dump") else b
                insight = Insight(
                    category=b_dict.get("category", "未分类"),
                    core_thesis=b_dict.get("core_thesis", ""),
                    logic_chain=b_dict.get("logic_chain", []),
                    historical_insight=b_dict.get("historical_insight"),
                    sources=b_dict.get("sources", []),
                    confidence_score=b_dict.get("confidence_score", 0.0),
                    date_generated=date.today(),
                )
                session.add(insight)
            await session.commit()
    except Exception as e:
        logger.error(f"[Scheduler] Failed to save to DB: {e}")


async def _cleanup_old_insights(days: int = 7):
    """清理 N 天前的旧洞见数据"""
    try:
        from sqlalchemy import delete
        from app.models.db.base import get_session_factory
        from app.models.db.insight import Insight
        from datetime import timedelta

        cutoff = date.today() - timedelta(days=days)
        session_factory = get_session_factory()
        async with session_factory() as session:
            stmt = delete(Insight).where(Insight.date_generated < cutoff)
            result = await session.execute(stmt)
            await session.commit()
            if result.rowcount > 0:
                logger.info(f"[Scheduler] Cleaned up {result.rowcount} old insights (before {cutoff})")
    except Exception as e:
        logger.warning(f"[Scheduler] Cleanup failed: {e}")


def start_scheduler():
    """启动 APScheduler（在 FastAPI lifespan 中调用）"""
    if not settings.SCHEDULER_ENABLED:
        logger.info("[Scheduler] Disabled by config")
        return None

    try:
        from apscheduler.schedulers.asyncio import AsyncIOScheduler
        from apscheduler.triggers.interval import IntervalTrigger

        scheduler = AsyncIOScheduler()
        from datetime import timedelta

        scheduler.add_job(
            run_scheduled_workflow,
            trigger=IntervalTrigger(minutes=settings.SCHEDULER_INTERVAL_MINUTES),
            id="insight_workflow",
            name="Insight Workflow 定时执行",
            replace_existing=True,
            # 启动后延迟 60 秒执行第一次（让服务先启动完成）
            next_run_time=datetime.now() + timedelta(seconds=60),
        )
        scheduler.start()
        logger.info(
            f"[Scheduler] Started — every {settings.SCHEDULER_INTERVAL_MINUTES} minutes, "
            f"platforms: {settings.NEWSNOW_PLATFORMS}"
        )
        return scheduler

    except ImportError:
        logger.error("[Scheduler] APScheduler not installed — run: pip install apscheduler")
        return None
    except Exception as e:
        logger.error(f"[Scheduler] Failed to start: {e}")
        return None
