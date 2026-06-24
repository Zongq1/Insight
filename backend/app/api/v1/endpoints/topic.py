"""主题管理 API 端点"""

from datetime import datetime
from typing import Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

router = APIRouter()


class TopicCreate(BaseModel):
    """创建主题请求模型"""

    name: str = Field(..., min_length=1, max_length=100, description="主题名称")
    keywords: list[str] = Field(..., min_length=1, description="关键词列表")


class TopicResponse(BaseModel):
    """主题响应模型"""

    id: str
    name: str
    keywords: list[str]
    last_fetched_at: Optional[datetime]
    created_at: datetime


class TopicListResponse(BaseModel):
    """主题列表响应模型"""

    items: list[TopicResponse]
    total: int


@router.get("", response_model=TopicListResponse)
async def list_topics() -> TopicListResponse:
    """获取所有主题列表"""
    # TODO: 从数据库查询主题列表

    return TopicListResponse(items=[], total=0)


@router.post("", response_model=TopicResponse, status_code=201)
async def create_topic(topic: TopicCreate) -> TopicResponse:
    """创建新主题

    添加一个新的监控主题，系统将定期检索相关信息。
    """
    # TODO: 创建主题并保存到数据库
    # new_topic = await topic_repo.create(topic)

    raise HTTPException(status_code=501, detail="Not implemented yet")


@router.get("/{topic_id}", response_model=TopicResponse)
async def get_topic(topic_id: str) -> TopicResponse:
    """获取主题详情"""
    # TODO: 从数据库查询主题
    # topic = await topic_repo.get_by_id(topic_id)
    # if not topic:
    #     raise HTTPException(status_code=404, detail="Topic not found")

    raise HTTPException(status_code=404, detail="Topic not found")


@router.delete("/{topic_id}", status_code=204)
async def delete_topic(topic_id: str) -> None:
    """删除主题"""
    # TODO: 从数据库删除主题
    # await topic_repo.delete(topic_id)

    raise HTTPException(status_code=501, detail="Not implemented yet")
