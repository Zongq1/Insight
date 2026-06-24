"""Topic ORM 模型测试"""

import pytest
from datetime import datetime

from app.models.db.topic import Topic, TopicInsight


class TestTopic:
    """Topic 模型测试"""

    def test_topic_creation(self):
        """测试 Topic 创建"""
        topic = Topic(
            name="AI Technology",
            keywords=["artificial intelligence", "machine learning", "deep learning"],
        )

        assert topic.name == "AI Technology"
        assert len(topic.keywords) == 3
        assert topic.last_fetched_at is None

    def test_topic_repr(self):
        """测试 Topic 字符串表示"""
        topic = Topic(id=1, name="AI", keywords=["ai"])
        repr_str = repr(topic)

        assert "Topic" in repr_str
        assert "id=1" in repr_str
        assert "AI" in repr_str

    def test_topic_with_keywords(self):
        """测试包含多个关键词的 Topic"""
        keywords = ["python", "programming", "coding", "development"]
        topic = Topic(name="Python", keywords=keywords)

        assert topic.keywords == keywords
        assert "python" in topic.keywords
        assert "programming" in topic.keywords

    def test_topic_last_fetched(self):
        """测试 last_fetched_at 字段"""
        now = datetime.utcnow()
        topic = Topic(
            name="Blockchain",
            keywords=["blockchain", "crypto"],
            last_fetched_at=now,
        )

        assert topic.last_fetched_at == now
        assert topic.last_fetched_at is not None


class TestTopicInsight:
    """TopicInsight 模型测试"""

    def test_topic_insight_creation(self):
        """测试 TopicInsight 创建"""
        relation = TopicInsight(
            topic_id=1,
            insight_id=10,
            relevance_score=0.85,
        )

        assert relation.topic_id == 1
        assert relation.insight_id == 10
        assert relation.relevance_score == 0.85

    def test_topic_insight_repr(self):
        """测试 TopicInsight 字符串表示"""
        relation = TopicInsight(id=1, topic_id=2, insight_id=3)
        repr_str = repr(relation)

        assert "TopicInsight" in repr_str
        assert "topic_id=2" in repr_str
        assert "insight_id=3" in repr_str

    def test_topic_insight_default_score(self):
        """测试默认相关性分数（需要显式设置）"""
        relation = TopicInsight(topic_id=1, insight_id=1, relevance_score=0.0)

        assert relation.relevance_score == 0.0

    def test_topic_insight_high_relevance(self):
        """测试高相关性"""
        relation = TopicInsight(
            topic_id=1,
            insight_id=1,
            relevance_score=0.95,
        )

        assert relation.relevance_score > 0.9

    def test_topic_insight_medium_relevance(self):
        """测试中等相关性"""
        relation = TopicInsight(
            topic_id=1,
            insight_id=1,
            relevance_score=0.5,
        )

        assert 0.4 < relation.relevance_score < 0.6
