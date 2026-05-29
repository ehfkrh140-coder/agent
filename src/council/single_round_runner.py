import json
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Optional

from src.agent_config import AgentConfig
from src.agents.agent_runner import AgentRunner
from src.schemas.agent_response import AgentResponse
from src.schemas.council_session import CouncilFlowMetadata
from src.schemas.session_record import AgentRunResult


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

    def _build_review_context(self, original_user_message: str, chair_result: AgentRunResult) -> dict:
        return {
            "original_user_message": original_user_message,
            "chair_brief": _result_to_context(chair_result),
        }

    def _build_final_context(self, original_user_message: str, results_by_id: dict[str, AgentRunResult]) -> dict:
        return {
            "original_user_message": original_user_message,
            "agent_01_chair": _result_to_context(results_by_id[self.flow.chair_agent_id]),
            "agent_02_pro": _result_to_context(results_by_id["agent_02"]),
            "agent_03_con": _result_to_context(results_by_id["agent_03"]),
            "agent_04_risk": _result_to_context(results_by_id["agent_04"]),
        }

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

    def run(self, user_message: str, parallel: bool = False, max_workers: int = 2) -> tuple[list[AgentRunResult], CouncilFlowMetadata, dict, dict[str, dict], dict]:
        print("=== Single Round Council v1 ===")
        chair_result = self._run_agent(self.flow.chair_agent_id, user_message)
        results_by_id: dict[str, AgentRunResult] = {chair_result.agent_id: chair_result}

        review_context = self._build_review_context(user_message, chair_result)
        review_contexts = {agent_id: review_context for agent_id in self.flow.review_agent_ids}
        review_messages = {agent_id: _json_context(review_context) for agent_id in self.flow.review_agent_ids}
        review_results = self._run_review_agents(review_messages, parallel=parallel, max_workers=max_workers)
        for result in review_results:
            results_by_id[result.agent_id] = result

        final_context = self._build_final_context(user_message, results_by_id)
        final_result = self._run_agent(self.flow.final_agent_id, _json_context(final_context))
        results_by_id[final_result.agent_id] = final_result

        flow = self.flow.model_copy(update={"review_parallel": parallel, "max_workers": max_workers})
        ordered_results = [results_by_id[agent_id] for agent_id in [self.flow.chair_agent_id, *self.flow.review_agent_ids, self.flow.final_agent_id]]
        return ordered_results, flow, review_context, review_contexts, final_context
