"""成本追踪器测试"""

import pytest
from datetime import datetime, timezone

from app.core.exceptions import CostLimitExceededError
from app.services.llm.cost_tracker import CostTracker, CostSummary, TokenUsage


@pytest.fixture
def cost_tracker():
    """创建成本追踪器实例"""
    return CostTracker()


class TestCostTracker:
    """成本追踪器测试"""

    def test_calculate_cost_gpt4o(self, cost_tracker):
        """测试 GPT-4o 成本计算"""
        input_cost, output_cost, total_cost = cost_tracker.calculate_cost(
            model="gpt-4o",
            input_tokens=1000,
            output_tokens=500,
        )

        # GPT-4o: $2.50/1M input, $10.00/1M output
        assert input_cost == pytest.approx(1000 * 2.50 / 1_000_000)
        assert output_cost == pytest.approx(500 * 10.00 / 1_000_000)
        assert total_cost == pytest.approx(input_cost + output_cost)

    def test_calculate_cost_unknown_model(self, cost_tracker):
        """测试未知模型的成本计算（使用 GPT-4o 价格）"""
        input_cost, output_cost, total_cost = cost_tracker.calculate_cost(
            model="unknown-model",
            input_tokens=1000,
            output_tokens=500,
        )

        # 应该使用 GPT-4o 的价格
        assert input_cost == pytest.approx(1000 * 2.50 / 1_000_000)
        assert output_cost == pytest.approx(500 * 10.00 / 1_000_000)

    def test_record_usage(self, cost_tracker):
        """测试记录 Token 使用"""
        usage = cost_tracker.record_usage(
            model="gpt-4o",
            input_tokens=1000,
            output_tokens=500,
            metadata={"test": True},
        )

        assert isinstance(usage, TokenUsage)
        assert usage.model == "gpt-4o"
        assert usage.input_tokens == 1000
        assert usage.output_tokens == 500
        assert usage.total_cost > 0
        assert usage.metadata == {"test": True}

    def test_check_budget_initial(self, cost_tracker):
        """测试初始预算状态"""
        summary = cost_tracker.check_budget()

        assert isinstance(summary, CostSummary)
        assert summary.daily_cost == 0.0
        assert summary.monthly_cost == 0.0
        assert summary.daily_usage_count == 0
        assert summary.monthly_usage_count == 0

    def test_check_budget_after_usage(self, cost_tracker):
        """测试使用后的预算状态"""
        # 记录一些使用
        cost_tracker.record_usage(
            model="gpt-4o",
            input_tokens=1000,
            output_tokens=500,
        )
        cost_tracker.record_usage(
            model="gpt-4o",
            input_tokens=2000,
            output_tokens=1000,
        )

        summary = cost_tracker.check_budget()

        assert summary.daily_cost > 0
        assert summary.daily_usage_count == 2
        assert summary.daily_remaining < summary.daily_budget

    def test_validate_budget_within_limit(self, cost_tracker):
        """测试预算内验证"""
        # 记录少量使用
        cost_tracker.record_usage(
            model="gpt-4o",
            input_tokens=100,
            output_tokens=50,
        )

        # 不应该抛出异常
        cost_tracker.validate_budget()

    def test_validate_budget_exceeded(self, cost_tracker):
        """测试预算超限验证"""
        # 模拟大量使用，超过每日预算
        # 每日预算默认 $50
        # GPT-4o: $2.50/1M input, $10.00/1M output
        # 每次调用: 100000 input + 50000 output = $0.25 + $0.50 = $0.75
        # 需要约 67 次调用来超过 $50
        for _ in range(70):
            cost_tracker.record_usage(
                model="gpt-4o",
                input_tokens=100000,
                output_tokens=50000,
            )

        with pytest.raises(CostLimitExceededError) as exc_info:
            cost_tracker.validate_budget()

        assert "Daily budget exceeded" in str(exc_info.value)

    def test_multiple_model_usage(self, cost_tracker):
        """测试多模型使用"""
        cost_tracker.record_usage(
            model="gpt-4o",
            input_tokens=1000,
            output_tokens=500,
        )
        cost_tracker.record_usage(
            model="claude-3-sonnet",
            input_tokens=2000,
            output_tokens=1000,
        )

        summary = cost_tracker.check_budget()

        assert summary.daily_usage_count == 2
        assert summary.daily_cost > 0
