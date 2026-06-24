"""最终洞见简报模型"""

import datetime
from typing import Optional

from pydantic import BaseModel, Field

from app.models.llm.logic_point import LogicPoint
from app.models.llm.source import Source


class FinalBriefing(BaseModel):
    """最终洞见简报

    系统输出的最终洞见卡片，包含核心论点、逻辑推演链和信息来源。
    这是 Instructor 结构化输出的核心数据模型。
    """

    date_generated: datetime.date = Field(
        default_factory=datetime.date.today,
        description="生成日期",
    )
    category: str = Field(
        ...,
        description="高维分类标签，最多三个单词，如 'AI Engineering' 或 'Quantum Computing'",
        min_length=1,
        max_length=50,
    )
    core_thesis: str = Field(
        ...,
        description="一句话概括核心论点，极其精炼，禁止使用形容词堆砌，字数控制在 40 字以内",
        min_length=10,
        max_length=200,
    )
    logic_chain: list[LogicPoint] = Field(
        ...,
        description="支撑核心论点的严密逻辑推演链，3-5个节点，层层递进",
        min_length=2,
        max_length=5,
    )
    historical_insight: Optional[str] = Field(
        default=None,
        description="系统检测到的历史知识脉络碰撞。如果此事件验证或推翻了历史记录，请指出来。若无关联则严格返回 null",
    )
    sources: list[Source] = Field(
        ...,
        description="信息来源列表",
        min_length=1,
    )
    confidence_score: float = Field(
        default=0.0,
        description="洞见置信度评分，范围 0-1，由 CriticNode 评估",
        ge=0.0,
        le=1.0,
    )

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "date_generated": "2024-01-15",
                    "category": "AI Infrastructure",
                    "core_thesis": "AI芯片需求爆发将推动半导体行业进入新一轮增长周期",
                    "logic_chain": [
                        {
                            "premise": "2024年Q1全球AI芯片出货量同比增长200%",
                            "conclusion": "AI基础设施需求正在爆发式增长",
                        },
                        {
                            "premise": "主要云厂商资本开支计划同比增长50%以上",
                            "conclusion": "企业级AI投资进入加速期",
                        },
                        {
                            "premise": "芯片产能扩张需要12-18个月",
                            "conclusion": "供需缺口将持续，推高芯片价格和利润率",
                        },
                    ],
                    "historical_insight": "这与2020年5G芯片需求爆发周期类似，但AI芯片的增长速度更快",
                    "sources": [
                        {"name": "TechCrunch", "url": "https://techcrunch.com/ai-chips"},
                        {"name": "Bloomberg", "url": "https://bloomberg.com/semiconductor"},
                    ],
                    "confidence_score": 0.85,
                }
            ]
        }
    }
