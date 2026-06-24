"""工作流 API 端点

提供多智能体工作流的 REST API。
"""

import logging
from datetime import date
from typing import Optional

from fastapi import APIRouter, BackgroundTasks, HTTPException
from pydantic import BaseModel, Field

from app.services.agents.workflow import InsightWorkflow

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/workflow", tags=["workflow"])

# 工作流执行状态存储
_workflow_states: dict[str, dict] = {}


class WorkflowRequest(BaseModel):
    """工作流请求"""

    topic: str = Field(..., min_length=1, description="目标主题")
    raw_texts: list[str] = Field(default_factory=list, description="预置原始文本（可选）")
    keywords: list[str] = Field(default_factory=list, description="搜索关键词（可选）")


class WorkflowResponse(BaseModel):
    """工作流响应"""

    thread_id: str = Field(..., description="执行线程 ID")
    status: str = Field(..., description="执行状态: running/completed/failed")
    final_briefings: list[dict] = Field(default_factory=list, description="最终洞见")
    errors: list[str] = Field(default_factory=list, description="错误信息")
    retry_count: int = Field(default=0, description="重试次数")


async def _run_workflow_background(
    thread_id: str,
    topic: str,
    raw_texts: list[str],
    keywords: list[str],
):
    """后台执行工作流"""
    try:
        workflow = InsightWorkflow()
        result = await workflow.run(
            topic=topic,
            raw_texts=raw_texts if raw_texts else None,
            keywords=keywords if keywords else None,
        )

        final_briefings = [
            b.model_dump() if hasattr(b, "model_dump") else b
            for b in result.get("final_briefings", [])
        ]

        # 保存到数据库
        await _save_briefings_to_db(final_briefings)

        _workflow_states[thread_id] = {
            "status": "completed",
            "final_briefings": final_briefings,
            "errors": result.get("errors", []),
            "retry_count": result.get("retry_count", 0),
        }

        logger.info(f"Workflow {thread_id} completed, saved {len(final_briefings)} insights to DB")

    except Exception as e:
        logger.error(f"Workflow {thread_id} failed: {e}")
        _workflow_states[thread_id] = {
            "status": "failed",
            "final_briefings": [],
            "errors": [str(e)],
            "retry_count": 0,
        }


async def _save_briefings_to_db(briefings: list[dict]):
    """将 workflow 结果保存到数据库"""
    try:
        from app.models.db.base import get_session_factory
        from app.models.db.insight import Insight

        session_factory = get_session_factory()
        async with session_factory() as session:
            for b in briefings:
                insight = Insight(
                    category=b.get("category", "未分类"),
                    core_thesis=b.get("core_thesis", ""),
                    logic_chain=b.get("logic_chain", []),
                    historical_insight=b.get("historical_insight"),
                    sources=b.get("sources", []),
                    confidence_score=b.get("confidence_score", 0.0),
                    date_generated=date.today(),
                )
                session.add(insight)
            await session.commit()
            logger.info(f"Saved {len(briefings)} insights to database")
    except Exception as e:
        logger.error(f"Failed to save briefings to DB: {e}")


@router.post("/run", response_model=WorkflowResponse)
async def run_workflow(
    request: WorkflowRequest,
    background_tasks: BackgroundTasks,
):
    """执行工作流

    异步执行多智能体工作流，立即返回 thread_id。
    通过 GET /workflow/status/{thread_id} 查询执行状态。
    """
    import uuid

    thread_id = str(uuid.uuid4())[:8]

    # 初始化状态
    _workflow_states[thread_id] = {
        "status": "running",
        "final_briefings": [],
        "errors": [],
        "retry_count": 0,
    }

    # 后台执行
    background_tasks.add_task(
        _run_workflow_background,
        thread_id=thread_id,
        topic=request.topic,
        raw_texts=request.raw_texts,
        keywords=request.keywords,
    )

    logger.info(f"Workflow {thread_id} started for topic: {request.topic}")

    return WorkflowResponse(
        thread_id=thread_id,
        status="running",
    )


@router.get("/status/{thread_id}", response_model=WorkflowResponse)
async def get_workflow_status(thread_id: str):
    """查询工作流执行状态"""
    state = _workflow_states.get(thread_id)

    if not state:
        raise HTTPException(status_code=404, detail=f"Workflow {thread_id} not found")

    return WorkflowResponse(
        thread_id=thread_id,
        status=state["status"],
        final_briefings=state["final_briefings"],
        errors=state["errors"],
        retry_count=state["retry_count"],
    )
