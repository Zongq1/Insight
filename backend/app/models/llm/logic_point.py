"""逻辑推演节点模型"""

from pydantic import BaseModel, Field


class LogicPoint(BaseModel):
    """逻辑推演节点

    表示逻辑推演链中的一个节点，包含推演前提和基于该前提得出的结论。
    """

    premise: str = Field(
        ...,
        description="推演前提或客观数据支撑",
        min_length=10,
        max_length=500,
    )
    conclusion: str = Field(
        ...,
        description="基于该前提得出的中间结论",
        min_length=10,
        max_length=500,
    )

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "premise": "2024年Q1全球AI芯片出货量同比增长200%",
                    "conclusion": "AI基础设施需求正在爆发式增长",
                }
            ]
        }
    }
