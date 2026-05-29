import json
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Optional

from src.agent_config import AgentConfig
from src.agents.agent_runner import AgentRunner
from src.schemas.agent_response import AgentResponse
from src.schemas.council_session import CouncilFlowMetadata
from src.schemas.opportunity_packet import OpportunityPacket
from src.schemas.session_record import AgentRunResult
from src.strategy.readiness import build_readiness_report

CHAIR_INSTRUCTION = "opportunity_packet을 회의 가능한 브리프로 정리하라. readiness_report를 우선 참고하라. active strategy가 아니면 experimental로 취급하라. readiness_pass=false이면 ENTER를 금지한다. last_price_only_candidate이면 수익 기회로 과장하지 말라. mark_orderbook_gap은 현재 active v1 전략이 아니므로 실험 전략으로만 논의하라. 여러 observations와 candidates가 있으면 모두 요약하라. 없는 데이터는 추정하지 말라. human_context가 있으면 시장 데이터와 분리해 정리하라."
REVIEW_INSTRUCTIONS = {
    "agent_02": ("pro_opportunity", "조건부 수익 가능성이 성립하려면 필요한 조건을 검토하라. readiness_report를 우선 참고하라. readiness_pass=false이면 ENTER를 금지한다. last_price_only_candidate이면 수익 기회로 과장하지 말라. active strategy가 아니면 experimental로 취급하라. 여러 candidates가 있으면 조건부로 유망한 후보를 분리하라. 없는 데이터는 추정하지 말라. human_context.thesis가 있으면 검토할 가설로만 다뤄라."),
    "agent_03": ("skeptic", "가짜 기회, 데이터 오류, 비용, 체결 불가능성, 시세 지연 가능성을 공격하라. readiness_report를 우선 참고하라. readiness_pass=false이면 ENTER를 금지한다. last_price_only_candidate이면 수익 기회로 과장하지 말라. active strategy가 아니면 experimental로 취급하라. 여러 candidates가 있으면 데이터 품질이 낮거나 비용 반영이 부족한 후보를 지적하라. human_context가 공격적이면 편향/과신 가능성을 검토하라."),
    "agent_04": ("risk_manager", "deterministic 실행부가 나중에 확인해야 할 risk gate와 중단 조건을 정리하라. readiness_report를 우선 참고하라. readiness_pass=false이면 ENTER를 금지한다. last_price_only_candidate이면 수익 기회로 과장하지 말라. active strategy가 아니면 experimental로 취급하라. 여러 venues가 있으면 venue별 risk gate를 구분하라. human_context.constraints는 더 엄격한 제한 조건으로 반영할 수 있다."),
}
FINAL_INSTRUCTION = "agent_01~04 결과를 종합해 ENTER/WATCH/REJECT/NEED_DATA 성향을 정리하라. readiness_report를 우선 참고하라. readiness_pass=false이면 ENTER를 금지한다. last_price_only_candidate이면 수익 기회로 과장하지 말라. active strategy가 아니면 experimental로 취급하라. mark_orderbook_gap은 현재 active v1 전략이 아니므로 실험 전략으로만 논의하라. 실행 지시는 금지한다. 여러 candidates가 있으면 가장 안전하고 데이터 품질이 높은 후보와 제외할 후보를 분리하라. human_context가 있으면 데이터 기반 판단과 사용자 의견 반영분을 분리하라. human_context.veto=true이면 진입 강제는 불가하고 보류/거부 성향을 강하게 반영하라."

ACTIVE_SPOT_SCOPE_INSTRUCTION = (
    "현재 active v1은 public spot bid/ask/orderbook 기반 분석이다. "
    "last_price 차이만으로 수익 기회 판단 금지. "
    "source ask와 target bid 또는 VWAP 기준으로만 검토하라. "
    "readiness_report를 우선 참고하고 readiness_pass=false이면 ENTER 금지. "
    "private endpoint, 잔고 조회, 주문, 출금, 이체, 자동매매는 현재 범위 밖이다. "
    "suggested_next_steps는 public market data 재검증, fee config 확인, depth/VWAP/slippage, "
    "timestamp/data_age/latency 확인으로 제한한다. "
    "입출금/전송/잔고는 현재 active v1의 required data가 아니며 execution 단계 전에는 "
    "필수 next step으로 제안하지 말 것. 실제 실행 지시는 금지한다."
)

EXPERIMENTAL_MARK_SCOPE_INSTRUCTION = (
    "mark_orderbook_gap은 experimental/disabled 전략이다. "
    "현재 active v1 전략이 아니므로 실험 전략으로만 논의하고 기본 판단 흐름에 사용하지 말 것."
)


def _strategy_scope_instruction(opportunity_packet: Optional[OpportunityPacket]) -> str:
    if not opportunity_packet:
        return ""
    if opportunity_packet.strategy_family == "cross_exchange_spot_spread":
        return ACTIVE_SPOT_SCOPE_INSTRUCTION
    if opportunity_packet.strategy_family == "mark_orderbook_gap":
        return EXPERIMENTAL_MARK_SCOPE_INSTRUCTION
    return "active strategy가 아닌 strategy_family는 experimental 또는 future로 취급하라."


def _with_strategy_scope(instruction: str, opportunity_packet: Optional[OpportunityPacket]) -> str:
    scope = _strategy_scope_instruction(opportunity_packet)
    return f"{instruction} {scope}" if scope else instruction


def _response_to_dict(response: Optional[AgentResponse]) -> Optional[dict]:
    return response.model_dump() if response is not None else None


def _result_to_context(result: AgentRunResult) -> dict:
    return {
        "agent_id": result.agent_id,
        "name": result.name,
        "status": result.status,
        "warning": result.warning,
        "error": result.error,
        "response": _response_to_dict(result.response),
    }


def _json_context(context: dict) -> str:
    return json.dumps(context, ensure_ascii=False, indent=2)


def packet_agent_dict(opportunity_packet: Optional[OpportunityPacket]) -> Optional[dict]:
    return opportunity_packet.agent_context_dict() if opportunity_packet else None


def packet_readiness_report(opportunity_packet: Optional[OpportunityPacket]) -> Optional[dict]:
    return build_readiness_report(opportunity_packet) if opportunity_packet else None


class SingleRoundCouncilRunner:
    def __init__(self, agent_configs: list[AgentConfig]):
        self.agent_configs_by_id = {config.agent_id: config for config in agent_configs}
        self.flow = CouncilFlowMetadata()
        self._validate_required_agents()

    def _validate_required_agents(self) -> None:
        required = [self.flow.chair_agent_id, *self.flow.review_agent_ids, self.flow.final_agent_id]
        missing = [agent_id for agent_id in required if agent_id not in self.agent_configs_by_id]
        if missing:
            raise ValueError(f"Missing council agent configs: {', '.join(missing)}")

    def _run_agent(self, agent_id: str, message: str) -> AgentRunResult:
        runner = AgentRunner([self.agent_configs_by_id[agent_id]])
        return runner.run_all(message, parallel=False)[0]

    @staticmethod
    def build_original_user_message(user_message: str, opportunity_packet: Optional[OpportunityPacket]) -> str:
        return opportunity_packet.summary_message() if opportunity_packet else user_message

    def _build_chair_context(self, original_user_message: str, opportunity_packet: Optional[OpportunityPacket]) -> dict:
        context = {
            "council_mode": self.flow.mode,
            "stage": "chair",
            "instruction": _with_strategy_scope(CHAIR_INSTRUCTION, opportunity_packet),
            "original_user_message": original_user_message,
        }
        if opportunity_packet:
            context["opportunity_packet"] = opportunity_packet.agent_context_dict()
            context["readiness_report"] = build_readiness_report(opportunity_packet)
        return context

    def _build_review_context(self, original_user_message: str, chair_result: AgentRunResult, opportunity_packet: Optional[OpportunityPacket], agent_id: str = "agent_02") -> dict:
        role, instruction = REVIEW_INSTRUCTIONS[agent_id]
        context = {
            "council_mode": self.flow.mode,
            "stage": "review",
            "review_role": role,
            "instruction": _with_strategy_scope(instruction, opportunity_packet),
            "original_user_message": original_user_message,
            "chair_brief": _result_to_context(chair_result),
        }
        if opportunity_packet:
            context["opportunity_packet"] = opportunity_packet.agent_context_dict()
            context["readiness_report"] = build_readiness_report(opportunity_packet)
        return context

    def _build_final_context(self, original_user_message: str, results_by_id: dict[str, AgentRunResult], opportunity_packet: Optional[OpportunityPacket]) -> dict:
        context = {
            "council_mode": self.flow.mode,
            "stage": "final",
            "instruction": _with_strategy_scope(FINAL_INSTRUCTION, opportunity_packet),
            "original_user_message": original_user_message,
            "agent_01_chair": _result_to_context(results_by_id[self.flow.chair_agent_id]),
            "agent_02_pro": _result_to_context(results_by_id["agent_02"]),
            "agent_03_con": _result_to_context(results_by_id["agent_03"]),
            "agent_04_risk": _result_to_context(results_by_id["agent_04"]),
        }
        if opportunity_packet:
            context["opportunity_packet"] = opportunity_packet.agent_context_dict()
            context["readiness_report"] = build_readiness_report(opportunity_packet)
        return context

    def build_dry_run_contexts(self, user_message: str, opportunity_packet: Optional[OpportunityPacket] = None) -> tuple[dict, dict[str, dict], dict]:
        original_user_message = self.build_original_user_message(user_message, opportunity_packet)
        chair_context = self._build_chair_context(original_user_message, opportunity_packet)
        empty_chair = AgentRunResult(agent_id="agent_01", name="Agent 01", status="dry_run", model="none", provider="dry_run")
        review_contexts = {
            agent_id: self._build_review_context(original_user_message, empty_chair, opportunity_packet, agent_id=agent_id)
            for agent_id in self.flow.review_agent_ids
        }
        empty_results = {
            "agent_01": empty_chair,
            "agent_02": AgentRunResult(agent_id="agent_02", name="Agent 02", status="dry_run", model="none", provider="dry_run"),
            "agent_03": AgentRunResult(agent_id="agent_03", name="Agent 03", status="dry_run", model="none", provider="dry_run"),
            "agent_04": AgentRunResult(agent_id="agent_04", name="Agent 04", status="dry_run", model="none", provider="dry_run"),
        }
        final_context = self._build_final_context(original_user_message, empty_results, opportunity_packet)
        return chair_context, review_contexts, final_context

    def _run_review_agents(self, review_messages: dict[str, str], parallel: bool, max_workers: int) -> list[AgentRunResult]:
        if not parallel:
            return [self._run_agent(agent_id, review_messages[agent_id]) for agent_id in self.flow.review_agent_ids]

        ordered: dict[str, AgentRunResult] = {}
        with ThreadPoolExecutor(max_workers=max(1, max_workers)) as executor:
            futures = {
                executor.submit(self._run_agent, agent_id, review_messages[agent_id]): agent_id
                for agent_id in self.flow.review_agent_ids
            }
            for future in as_completed(futures):
                agent_id = futures[future]
                ordered[agent_id] = future.result()
        return [ordered[agent_id] for agent_id in self.flow.review_agent_ids]

    def run(self, user_message: str, parallel: bool = False, max_workers: int = 2, opportunity_packet: Optional[OpportunityPacket] = None, scenario_name: Optional[str] = None) -> tuple[list[AgentRunResult], CouncilFlowMetadata, dict, dict[str, dict], dict]:
        print("=== Single Round Council v1 ===")
        original_user_message = self.build_original_user_message(user_message, opportunity_packet)
        chair_context = self._build_chair_context(original_user_message, opportunity_packet)
        chair_message = _json_context(chair_context) if opportunity_packet else user_message
        chair_result = self._run_agent(self.flow.chair_agent_id, chair_message)
        results_by_id: dict[str, AgentRunResult] = {chair_result.agent_id: chair_result}

        review_contexts = {
            agent_id: self._build_review_context(original_user_message, chair_result, opportunity_packet, agent_id=agent_id)
            for agent_id in self.flow.review_agent_ids
        }
        review_messages = {agent_id: _json_context(review_contexts[agent_id]) for agent_id in self.flow.review_agent_ids}
        review_results = self._run_review_agents(review_messages, parallel=parallel, max_workers=max_workers)
        for result in review_results:
            results_by_id[result.agent_id] = result

        final_context = self._build_final_context(original_user_message, results_by_id, opportunity_packet)
        final_result = self._run_agent(self.flow.final_agent_id, _json_context(final_context))
        results_by_id[final_result.agent_id] = final_result

        flow = self.flow.model_copy(update={"review_parallel": parallel, "max_workers": max_workers})
        ordered_results = [results_by_id[agent_id] for agent_id in [self.flow.chair_agent_id, *self.flow.review_agent_ids, self.flow.final_agent_id]]
        return ordered_results, flow, chair_context, review_contexts, final_context
