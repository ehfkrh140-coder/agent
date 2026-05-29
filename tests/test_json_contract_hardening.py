import json
import re
import unittest
from pathlib import Path

from src.agents.generic_gemini_agent import GenericGeminiAgent


PROMPT_FILES = [Path("prompts") / f"agent_0{i}.md" for i in range(1, 6)]
EXPECTED_KEYS = {"summary", "key_points", "concerns", "questions", "suggested_next_steps", "confidence"}


class JsonContractHardeningTests(unittest.TestCase):
    def test_build_cli_prompt_includes_final_json_contract(self):
        prompt = GenericGeminiAgent._build_cli_prompt("system", "안녕?")

        required_phrases = [
            "최종 출력 계약:",
            "JSON validator에 직접 들어갑니다",
            "JSON 파싱에 실패하면 전체 agent run은 실패입니다",
            "사용자 입력이 인사, 잡담, hello, 테스트여도 반드시 AgentResponse JSON 객체 하나만 출력합니다",
            "절대 자기소개하지 않습니다",
            "절대 도움 요청, 추가 지시 요청, 자료 제공 요청, 사용자 승인 요청을 하지 않습니다",
            "첫 글자는 반드시 { 이어야 합니다",
            "마지막 글자는 반드시 } 이어야 합니다",
            "허용 키 외 키를 추가하지 않습니다",
            "도구를 호출하지 말고 최종 답변만 생성합니다",
            "비시장 입력이면 summary에 거래소 매매 판단 데이터가 제공되지 않음을 쓰고, concerns에 시장 데이터 부족을 포함합니다",
        ]
        for phrase in required_phrases:
            self.assertIn(phrase, prompt)

    def test_prompts_include_non_market_json_only_contract(self):
        required_phrases = [
            "JSON Contract Hardening v2:",
            "첫 글자는 반드시 { 이어야 합니다.",
            "마지막 글자는 반드시 } 이어야 합니다.",
            "JSON 객체 외 텍스트는 실패로 간주합니다.",
            "인사말, 자기소개, 역할 확인, 초기화 완료, 준비 완료 문구를 출력하지 않습니다.",
            "비시장 입력이면 summary에 \"거래소 매매 판단 데이터가 제공되지 않음\"을 적고, concerns에 \"시장 데이터 부족\"을 넣습니다.",
            "questions는 사용자에게 대화형 질문을 던지는 곳이 아니라, 판단에 필요한 데이터 항목을 나열하는 곳입니다.",
            "suggested_next_steps는 실행/주문이 아니라 확인할 데이터 항목만 적습니다.",
            "절대 workspace, repository, file system, tool, command, shell, grep, read_file, write_file을 언급하지 않습니다.",
            "허용 키는 summary, key_points, concerns, questions, suggested_next_steps, confidence 뿐입니다.",
        ]

        for path in PROMPT_FILES:
            text = path.read_text(encoding="utf-8")
            with self.subTest(path=path):
                for phrase in required_phrases:
                    self.assertIn(phrase, text)

    def test_prompt_json_skeleton_uses_only_agent_response_keys(self):
        for path in PROMPT_FILES:
            text = path.read_text(encoding="utf-8")
            match = re.search(r"JSON schema:\s*(\{.*\})\s*$", text, flags=re.DOTALL)
            with self.subTest(path=path):
                self.assertIsNotNone(match)
                skeleton = json.loads(match.group(1))
                self.assertEqual(set(skeleton.keys()), EXPECTED_KEYS)
                self.assertIsInstance(skeleton["summary"], str)
                self.assertIsInstance(skeleton["key_points"], list)
                self.assertIsInstance(skeleton["concerns"], list)
                self.assertIsInstance(skeleton["questions"], list)
                self.assertIsInstance(skeleton["suggested_next_steps"], list)
                self.assertIsInstance(skeleton["confidence"], float)


if __name__ == "__main__":
    unittest.main()
