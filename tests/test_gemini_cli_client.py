import json
import unittest

from src.llm.gemini_cli_client import GeminiCliClient
from src.schemas.agent_response import AgentResponse


class GeminiCliClientParsingTests(unittest.TestCase):
    def test_parse_agent_response_with_code_block_and_noise(self):
        inner = {
            "summary": "요약",
            "key_points": ["a"],
            "concerns": ["b"],
            "questions": ["c"],
            "suggested_next_steps": ["d"],
            "confidence": 0.9,
        }
        response_text = "```json\n" + json.dumps(inner, ensure_ascii=False) + "\n```"
        outer = {"response": response_text}
        sample_stdout = "rg: warning text\n" + json.dumps(outer, ensure_ascii=False) + "\ntrailing"

        parsed = GeminiCliClient.parse_agent_response_from_stdout(sample_stdout, AgentResponse)
        self.assertEqual(parsed.summary, "요약")
        self.assertEqual(parsed.key_points, ["a"])
        self.assertAlmostEqual(parsed.confidence, 0.9)


if __name__ == "__main__":
    unittest.main()
