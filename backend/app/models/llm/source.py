"""信息来源模型"""

from pydantic import BaseModel, Field, field_validator


class Source(BaseModel):
    """信息来源

    记录洞见的原始信息来源，包括来源名称和原文链接。
    """

    name: str = Field(
        ...,
        description="信息来源名称，如 'Arxiv', 'TechCrunch', 'GitHub Repo'",
        min_length=1,
        max_length=100,
    )
    url: str = Field(
        ...,
        description="原文绝对链接，必须是合法的 URL 格式",
    )

    @field_validator("url")
    @classmethod
    def validate_url(cls, v: str) -> str:
        """验证 URL 格式"""
        if not v.startswith(("http://", "https://")):
            raise ValueError("URL 必须包含 http/https 协议头")
        return v

    model_config = {
        "json_schema_extra": {
            "examples": [
                {"name": "TechCrunch", "url": "https://techcrunch.com/2024/01/01/article"},
                {"name": "Arxiv", "url": "https://arxiv.org/abs/2401.00001"},
            ]
        }
    }
