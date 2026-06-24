"""InsightWorkflow - LangGraph DAG 组装

组装 Scout -> Distiller -> Critic -> Editor 的有向无环图，
实现多智能体协同的洞见精炼流程。
"""

import logging
from typing import Any

from langgraph.graph import END, START, StateGraph

from app.core.state import GraphState
from app.models.llm import FinalBriefing
from app.services.agents.critic import CriticNode, critic_node
from app.services.agents.distiller import DistillerNode, distiller_node
from app.services.agents.editor import MemoryEditorNode, memory_editor_node
from app.services.agents.scout import ScoutNode, scout_node

try:
    from langgraph.checkpoint.postgres.aio import AsyncPostgresSaver

    _HAS_POSTGRES_CHECKPOINTER = True
except ImportError:
    _HAS_POSTGRES_CHECKPOINTER = False

logger = logging.getLogger(__name__)

# 最大重试次数（0 = 禁用 Reflexion 重试，加速执行）
MAX_RETRY_COUNT = 0


class InsightWorkflow:
    """InsightWorkflow - 多智能体协同工作流

    组装 LangGraph DAG:
    Scout -> Distiller -> Critic -> (Approved) -> Editor
                                   -> (Rejected) -> Distiller (retry)
    """

    def __init__(
        self,
        scout: ScoutNode | None = None,
        distiller: DistillerNode | None = None,
        critic: CriticNode | None = None,
        editor: MemoryEditorNode | None = None,
        max_retry: int = MAX_RETRY_COUNT,
        checkpointer: Any | None = None,
    ):
        self.scout = scout or scout_node
        self.distiller = distiller or distiller_node
        self.critic = critic or critic_node
        self.editor = editor or memory_editor_node
        self.max_retry = max_retry
        self._checkpointer = checkpointer

        # 构建 LangGraph
        self.graph = self._build_graph()

    def _build_graph(self) -> Any:
        """构建 LangGraph DAG"""
        workflow = StateGraph(GraphState)

        # 注册节点
        workflow.add_node("scout", self._scout_node)
        workflow.add_node("distiller", self._distiller_node)
        workflow.add_node("critic", self._critic_node)
        workflow.add_node("editor", self._editor_node)

        # 定义边
        workflow.add_edge(START, "scout")
        workflow.add_edge("scout", "distiller")
        workflow.add_edge("distiller", "critic")

        # 条件边: Critic 决定是否通过
        # 直接结束，跳过 Editor（历史关联耗时且非核心）
        workflow.add_conditional_edges(
            "critic",
            self._route_after_critic,
            {
                "approved": END,
                "rejected": "distiller",  # 重试
                "max_retries_reached": END,
            },
        )

        return workflow.compile(checkpointer=self._checkpointer)

    async def _scout_node(self, state: GraphState) -> dict:
        """Scout 节点: 搜索原始文本

        如果 raw_texts 已有内容（外部注入），则跳过搜索。
        否则使用 LLM 生成搜索策略（不传 keywords 触发 LLM 策略）。
        """
        topic = state.get("target_topic", "")

        # 如果已有 raw_texts，跳过 Scout
        if state.get("raw_texts"):
            logger.info(
                f"Scout: raw_texts already present ({len(state['raw_texts'])}), skipping search"
            )
            return {}

        if not topic:
            logger.warning("Scout: no target_topic provided")
            return {"errors": ["No target topic provided"]}

        try:
            # 直接搜索，跳过 LLM 策略生成（RSS 源不需要关键词策略）
            result = await self.scout.search_topic(topic, keywords=[topic])

            logger.info(f"Scout: found {len(result.raw_texts)} raw texts")
            return {"raw_texts": result.raw_texts}

        except Exception as e:
            logger.error(f"Scout error: {e}")
            return {"errors": [f"Scout error: {str(e)}"]}

    async def _distiller_node(self, state: GraphState) -> dict:
        """Distiller 节点: 提纯原始文本为洞见

        处理所有 raw_texts，生成 FinalBriefing 列表。
        如果存在 Critic 先前反馈（Reflexion），注入到 Distiller prompt 中。
        """
        raw_texts = state.get("raw_texts", [])
        topic = state.get("target_topic", "")
        prior_feedback = state.get("critic_feedback_text") or None

        if not raw_texts:
            logger.warning("Distiller: no raw texts to process")
            return {"draft_insights": []}

        if prior_feedback:
            logger.info("Distiller: Reflexion mode — injecting prior feedback")

        try:
            # 提纯所有文本（如有反馈则传入）
            briefings = await self.distiller.distill_batch(
                raw_texts, topic, prior_feedback=prior_feedback
            )

            # 转换为 dict 存储到 state
            draft_insights = [b.model_dump() for b in briefings]

            logger.info(f"Distiller: produced {len(draft_insights)} draft insights")
            return {"draft_insights": draft_insights}

        except Exception as e:
            logger.error(f"Distiller error: {e}")
            return {"errors": [f"Distiller error: {str(e)}"]}

    async def _critic_node(self, state: GraphState) -> dict:
        """Critic 节点: 评审洞见质量

        逐条评审 draft_insights，决定是否通过。
        """
        draft_insights = state.get("draft_insights", [])

        if not draft_insights:
            logger.warning("Critic: no draft insights to review")
            return {"critic_feedback": ["No insights to review"]}

        try:
            # 将 dict 转换回 FinalBriefing 对象
            briefings = []
            for d in draft_insights:
                try:
                    briefings.append(FinalBriefing(**d))
                except Exception as e:
                    logger.error(f"Failed to parse draft insight: {e}")
                    continue

            if not briefings:
                return {"critic_feedback": ["All draft insights failed to parse"]}

            # 评审所有洞见
            reviews = await self.critic.review_batch(briefings)

            # 收集通过的洞见
            approved_insights = []
            feedback_list = []
            rejected_feedbacks = []

            for i, (briefing, review) in enumerate(zip(briefings, reviews)):
                if review.is_approved:
                    approved_insights.append(briefing)
                    feedback_list.append(
                        f"Insight {i + 1}: APPROVED (confidence={review.confidence_score:.2f})"
                    )
                else:
                    feedback_list.append(
                        f"Insight {i + 1}: REJECTED (confidence={review.confidence_score:.2f}) - "
                        f"{review.feedback}"
                    )
                    rejected_feedbacks.append(
                        f"Insight {i + 1}: {review.feedback}"
                    )

            # 构建 Reflexion 反馈文本（供 Distiller 重试使用）
            critic_feedback_text = ""
            if rejected_feedbacks:
                critic_feedback_text = (
                    "The following insights were rejected by the Critic:\n\n"
                    + "\n".join(rejected_feedbacks)
                )

            # 更新 retry_count
            current_retry = state.get("retry_count", 0)

            logger.info(
                f"Critic: {len(approved_insights)}/{len(briefings)} approved, "
                f"retry_count={current_retry}"
            )

            return {
                "final_briefings": approved_insights,
                "critic_feedback": feedback_list,
                "critic_feedback_text": critic_feedback_text,
                "retry_count": current_retry,
            }

        except Exception as e:
            logger.error(f"Critic error: {e}")
            return {"errors": [f"Critic error: {str(e)}"]}

    async def _editor_node(self, state: GraphState) -> dict:
        """Editor 节点: 记忆映射，关联历史脉络

        对通过评审的洞见执行向量检索和历史关联。
        """
        final_briefings = state.get("final_briefings", [])
        topic = state.get("target_topic", "")

        if not final_briefings:
            logger.warning("Editor: no final briefings to process")
            return {}

        try:
            processed = await self.editor.process_batch(final_briefings, topic)

            logger.info(f"Editor: processed {len(processed)} insights")
            return {"final_briefings": processed}

        except Exception as e:
            logger.error(f"Editor error: {e}")
            return {"errors": [f"Editor error: {str(e)}"]}

    def _route_after_critic(self, state: GraphState) -> str:
        """Critic 后的路由决策

        判断是否需要重试或直接结束。
        """
        final_briefings = state.get("final_briefings", [])
        retry_count = state.get("retry_count", 0)

        # 如果有通过的洞见，直接结束
        if final_briefings:
            logger.info(f"Routing: {len(final_briefings)} approved -> end")
            return "approved"

        # 如果禁用重试或超过最大重试次数，结束
        if self.max_retry <= 0 or retry_count >= self.max_retry:
            logger.warning("Routing: no approved insights, max retries reached -> end")
            return "max_retries_reached"

        # 否则重试
        logger.info(f"Routing: rejected -> retry (attempt {retry_count + 1})")
        return "rejected"

    async def run(
        self,
        topic: str,
        raw_texts: list[str] | None = None,
        keywords: list[str] | None = None,
        thread_id: str | None = None,
    ) -> dict:
        """执行完整工作流

        Args:
            topic: 目标主题
            raw_texts: 预置的原始文本（可选，跳过 Scout 搜索）
            keywords: 搜索关键词（可选，仅在无 raw_texts 时使用）
            thread_id: 线程 ID（可选，用于 checkpointer 状态持久化）

        Returns:
            最终状态字典
        """
        logger.info(f"Starting workflow for topic: {topic}")

        # 初始化状态
        initial_state: GraphState = {
            "target_topic": topic,
            "raw_texts": raw_texts or [],
            "draft_insights": [],
            "critic_feedback": [],
            "final_briefings": [],
            "retry_count": 0,
            "current_index": 0,
            "errors": [],
        }

        # 构建 config（含 thread_id 用于 checkpointer）
        config = None
        if thread_id and self._checkpointer:
            config = {"configurable": {"thread_id": thread_id}}

        # 执行 DAG
        try:
            final_state = await self.graph.ainvoke(initial_state, config=config)

            logger.info(
                f"Workflow completed: {len(final_state.get('final_briefings', []))} final insights, "
                f"retry_count={final_state.get('retry_count', 0)}"
            )

            return final_state

        except Exception as e:
            logger.error(f"Workflow execution failed: {e}")
            return {
                **initial_state,
                "errors": [f"Workflow failed: {str(e)}"],
            }


def _create_checkpointer() -> Any | None:
    """创建 checkpointer，优先使用 PostgreSQL，回退到 MemorySaver"""
    if _HAS_POSTGRES_CHECKPOINTER:
        try:
            from app.config import settings

            return AsyncPostgresSaver.from_conn_string(settings.DATABASE_URL)
        except Exception:
            logger.warning("PostgresCheckpointer init failed, falling back to no checkpointer")
    return None


# 全局工作流实例
insight_workflow = InsightWorkflow(checkpointer=_create_checkpointer())
