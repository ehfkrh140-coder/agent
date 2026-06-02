from __future__ import annotations

from src.schemas.council_session import ScenarioEvaluationMetadata
from src.schemas.opportunity_packet import OpportunityPacket
from src.schemas.session_record import AgentRunResult


def build_scenario_evaluation(opportunity_packet: OpportunityPacket | None, results: list[AgentRunResult] | None = None) -> ScenarioEvaluationMetadata:
    expected = opportunity_packet.expected_behavior if opportunity_packet else None
    expected_dict = expected.model_dump(mode="json") if expected else None
    final_result = None
    if results:
        final_result = next((r for r in results if r.agent_id == "agent_05"), None)
    final_response = final_result.response if final_result else None
    final_summary = final_response.summary if final_response else ""

    contains_expected = None
    confidence_within = None
    violations: list[str] = []
    if expected:
        if expected.acceptable_final_decisions or expected.preferred_final_decision:
            decisions = expected.acceptable_final_decisions or [expected.preferred_final_decision]
            contains_expected = any(d and d in final_summary for d in decisions) if final_response else None
        if expected.max_confidence is not None:
            confidence_within = final_response.confidence <= expected.max_confidence if final_response else None
        if final_response:
            response_text = "\n".join([
                final_response.summary,
                *final_response.key_points,
                *final_response.concerns,
                *final_response.questions,
                *final_response.suggested_next_steps,
            ])
            violations = [term for term in expected.must_not_include if term and term in response_text]

    return ScenarioEvaluationMetadata(
        expected_behavior_present=expected is not None,
        expected_behavior=expected_dict,
        final_summary_contains_expected_decision=contains_expected,
        final_confidence_within_expected_max=confidence_within,
        must_not_include_violations=violations,
    )
