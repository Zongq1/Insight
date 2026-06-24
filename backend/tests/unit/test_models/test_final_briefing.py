"""FinalBriefing 模型测试

验证 Pydantic 模型的正确性和 Instructor 结构化输出的稳定性。
"""

import datetime
from typing import Optional

import pytest
from pydantic import ValidationError

from app.models.llm import FinalBriefing, LogicPoint, Source


class TestSource:
    """Source 模型测试"""

    def test_valid_source(self) -> None:
        """测试有效的 Source 创建"""
        source = Source(
            name="TechCrunch",
            url="https://techcrunch.com/article",
        )
        assert source.name == "TechCrunch"
        assert source.url == "https://techcrunch.com/article"

    def test_invalid_url_missing_protocol(self) -> None:
        """测试无效 URL（缺少协议）"""
        with pytest.raises(ValidationError) as exc_info:
            Source(name="Test", url="example.com")

        assert "URL 必须包含 http/https 协议头" in str(exc_info.value)

    def test_valid_http_url(self) -> None:
        """测试 HTTP URL"""
        source = Source(name="Test", url="http://example.com")
        assert source.url == "http://example.com"

    def test_valid_https_url(self) -> None:
        """测试 HTTPS URL"""
        source = Source(name="Test", url="https://example.com")
        assert source.url == "https://example.com"

    def test_empty_name(self) -> None:
        """测试空名称"""
        with pytest.raises(ValidationError):
            Source(name="", url="https://example.com")


class TestLogicPoint:
    """LogicPoint 模型测试"""

    def test_valid_logic_point(self) -> None:
        """测试有效的 LogicPoint 创建"""
        point = LogicPoint(
            premise="2024年Q1全球AI芯片出货量同比增长200%",
            conclusion="AI基础设施需求正在爆发式增长",
        )
        assert "200%" in point.premise
        assert "爆发式增长" in point.conclusion

    def test_premise_too_short(self) -> None:
        """测试前提过短"""
        with pytest.raises(ValidationError):
            LogicPoint(premise="短", conclusion="这是一个有效的结论用于测试")

    def test_conclusion_too_short(self) -> None:
        """测试结论过短"""
        with pytest.raises(ValidationError):
            LogicPoint(premise="这是一个有效的前提用于测试验证", conclusion="短")


class TestFinalBriefing:
    """FinalBriefing 模型测试"""

    def test_valid_briefing(self) -> None:
        """测试有效的 FinalBriefing 创建"""
        briefing = FinalBriefing(
            category="AI Infrastructure",
            core_thesis="AI芯片需求爆发将推动半导体行业进入新一轮增长周期",
            logic_chain=[
                LogicPoint(
                    premise="2024年Q1全球AI芯片出货量同比增长200%",
                    conclusion="AI基础设施需求正在爆发式增长",
                ),
                LogicPoint(
                    premise="主要云厂商资本开支计划同比增长50%以上",
                    conclusion="企业级AI投资进入加速期",
                ),
            ],
            sources=[
                Source(name="TechCrunch", url="https://techcrunch.com/article"),
            ],
            confidence_score=0.85,
        )

        assert briefing.category == "AI Infrastructure"
        assert len(briefing.logic_chain) == 2
        assert briefing.confidence_score == 0.85
        assert briefing.date_generated == datetime.date.today()

    def test_briefing_with_historical_insight(self) -> None:
        """测试包含历史洞察的 FinalBriefing"""
        briefing = FinalBriefing(
            category="AI Infrastructure",
            core_thesis="AI芯片需求爆发将推动半导体行业进入新一轮增长周期",
            logic_chain=[
                LogicPoint(
                    premise="2024年Q1全球AI芯片出货量同比增长200%",
                    conclusion="AI基础设施需求正在爆发式增长",
                ),
                LogicPoint(
                    premise="主要云厂商资本开支计划同比增长50%以上",
                    conclusion="企业级AI投资进入加速期",
                ),
            ],
            sources=[
                Source(name="TechCrunch", url="https://techcrunch.com/article"),
            ],
            historical_insight="这与2020年5G芯片需求爆发周期类似",
        )

        assert briefing.historical_insight is not None
        assert "5G" in briefing.historical_insight

    def test_briefing_without_historical_insight(self) -> None:
        """测试不包含历史洞察的 FinalBriefing"""
        briefing = FinalBriefing(
            category="AI Infrastructure",
            core_thesis="AI芯片需求爆发将推动半导体行业进入新一轮增长周期",
            logic_chain=[
                LogicPoint(
                    premise="2024年Q1全球AI芯片出货量同比增长200%",
                    conclusion="AI基础设施需求正在爆发式增长",
                ),
                LogicPoint(
                    premise="主要云厂商资本开支计划同比增长50%以上",
                    conclusion="企业级AI投资进入加速期",
                ),
            ],
            sources=[
                Source(name="TechCrunch", url="https://techcrunch.com/article"),
            ],
        )

        assert briefing.historical_insight is None

    def test_logic_chain_too_short(self) -> None:
        """测试逻辑链过短（少于2个节点）"""
        with pytest.raises(ValidationError) as exc_info:
            FinalBriefing(
                category="AI",
                core_thesis="这是一个有效的核心论点用于测试验证",
                logic_chain=[
                    LogicPoint(
                        premise="这是一个有效的前提用于测试验证",
                        conclusion="这是一个有效的结论用于测试验证",
                    ),
                ],
                sources=[
                    Source(name="Test", url="https://example.com"),
                ],
            )

        error_str = str(exc_info.value)
        assert "2" in error_str or "at least" in error_str.lower() or "min_length" in error_str

    def test_logic_chain_too_long(self) -> None:
        """测试逻辑链过长（超过5个节点）"""
        logic_chain = [
            LogicPoint(
                premise=f"这是第{i}个有效的前提用于测试验证",
                conclusion=f"这是第{i}个有效的结论用于测试验证",
            )
            for i in range(6)
        ]

        with pytest.raises(ValidationError):
            FinalBriefing(
                category="AI",
                core_thesis="这是一个有效的核心论点用于测试验证",
                logic_chain=logic_chain,
                sources=[
                    Source(name="Test", url="https://example.com"),
                ],
            )

    def test_confidence_score_range(self) -> None:
        """测试置信度评分范围"""
        # 有效范围
        briefing = FinalBriefing(
            category="AI",
            core_thesis="这是一个有效的核心论点用于测试验证内容",
            logic_chain=[
                LogicPoint(
                    premise="这是一个有效的前提用于测试验证",
                    conclusion="这是一个有效的结论用于测试验证",
                ),
                LogicPoint(
                    premise="这是另一个有效的前提用于测试验证",
                    conclusion="这是另一个有效的结论用于测试验证",
                ),
            ],
            sources=[
                Source(name="Test", url="https://example.com"),
            ],
            confidence_score=0.5,
        )
        assert briefing.confidence_score == 0.5

        # 超出范围
        with pytest.raises(ValidationError):
            FinalBriefing(
                category="AI",
                core_thesis="这是一个有效的核心论点用于测试验证内容",
                logic_chain=[
                    LogicPoint(
                        premise="这是一个有效的前提用于测试验证",
                        conclusion="这是一个有效的结论用于测试验证",
                    ),
                    LogicPoint(
                        premise="这是另一个有效的前提用于测试验证",
                        conclusion="这是另一个有效的结论用于测试验证",
                    ),
                ],
                sources=[
                    Source(name="Test", url="https://example.com"),
                ],
                confidence_score=1.5,  # 超出 0-1 范围
            )

    def test_json_serialization(self) -> None:
        """测试 JSON 序列化"""
        briefing = FinalBriefing(
            category="AI Infrastructure",
            core_thesis="AI芯片需求爆发将推动半导体行业进入新一轮增长周期",
            logic_chain=[
                LogicPoint(
                    premise="2024年Q1全球AI芯片出货量同比增长200%",
                    conclusion="AI基础设施需求正在爆发式增长",
                ),
                LogicPoint(
                    premise="主要云厂商资本开支计划同比增长50%以上",
                    conclusion="企业级AI投资进入加速期",
                ),
            ],
            sources=[
                Source(name="TechCrunch", url="https://techcrunch.com/article"),
            ],
            confidence_score=0.85,
        )

        # 测试 model_dump
        data = briefing.model_dump()
        assert isinstance(data, dict)
        assert data["category"] == "AI Infrastructure"
        assert len(data["logic_chain"]) == 2

        # 测试 model_dump_json
        json_str = briefing.model_dump_json()
        assert isinstance(json_str, str)
        assert "AI Infrastructure" in json_str

    def test_json_deserialization(self) -> None:
        """测试 JSON 反序列化"""
        data = {
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
            ],
            "sources": [
                {"name": "TechCrunch", "url": "https://techcrunch.com/article"},
            ],
            "confidence_score": 0.85,
        }

        briefing = FinalBriefing.model_validate(data)
        assert briefing.category == "AI Infrastructure"
        assert briefing.date_generated == datetime.date(2024, 1, 15)
