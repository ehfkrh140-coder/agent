import json
import os
import re
import subprocess
from typing import Type

from pydantic import BaseModel


class GeminiCliClient:
    def __init__(self, cli_command: str = "gemini", timeout_seconds: int = 120):
        self.cli_command = cli_command
        self.timeout_seconds = timeout_seconds

    @staticmethod
    def _extract_first_json_object(text: str) -> str:
        start = text.find("{")
        if start < 0:
            raise ValueError("No JSON object start found in CLI stdout")

        depth = 0
        in_string = False
        escape = False
        for idx in range(start, len(text)):
            ch = text[idx]
            if in_string:
                if escape:
                    escape = False
                elif ch == "\\":
                    escape = True
                elif ch == '"':
                    in_string = False
            else:
                if ch == '"':
                    in_string = True
                elif ch == "{":
                    depth += 1
                elif ch == "}":
                    depth -= 1
                    if depth == 0:
                        return text[start : idx + 1]

        raise ValueError("No complete JSON object found in CLI stdout")

    @staticmethod
    def _strip_json_code_block(text: str) -> str:
        code_block = re.search(r"```json\s*(.*?)\s*```", text, flags=re.DOTALL | re.IGNORECASE)
        if code_block:
            return code_block.group(1).strip()
        return text.strip()

    @classmethod
    def parse_agent_response_from_stdout(cls, stdout: str, response_schema: Type[BaseModel]) -> BaseModel:
        outer_json_str = cls._extract_first_json_object(stdout)
        outer = json.loads(outer_json_str)

        response_text = outer.get("response")
        if not isinstance(response_text, str) or not response_text.strip():
            raise ValueError("Outer JSON does not contain a valid 'response' string")

        inner_json_text = cls._strip_json_code_block(response_text)
        inner = json.loads(inner_json_text)
        return response_schema.model_validate(inner)

    def generate_structured(
        self,
        *,
        prompt: str,
        response_schema: Type[BaseModel],
        gemini_cli_home: str,
    ) -> BaseModel:
        if not gemini_cli_home:
            raise ValueError("gemini_cli_home is required for gemini_cli provider")

        cmd = [
            self.cli_command,
            "--skip-trust",
            "-p",
            prompt,
            "--output-format",
            "json",
        ]

        env = os.environ.copy()
        env.update(
            {
                "GEMINI_CLI_HOME": gemini_cli_home,
                "GEMINI_FORCE_ENCRYPTED_FILE_STORAGE": "true",
                "GEMINI_FORCE_FILE_STORAGE": "true",
                "GEMINI_CLI_TRUST_WORKSPACE": "true",
            }
        )

        completed = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            env=env,
            timeout=self.timeout_seconds,
            shell=False,
        )

        stdout = completed.stdout or ""
        stderr = completed.stderr or ""

        if completed.returncode != 0:
            raise RuntimeError(
                f"Gemini CLI failed with code {completed.returncode}. stderr={stderr.strip()} stdout={stdout.strip()}"
            )

        try:
            return self.parse_agent_response_from_stdout(stdout, response_schema)
        except Exception as exc:
            raise ValueError(
                f"Failed to parse Gemini CLI output. stderr={stderr.strip()} stdout={stdout.strip()} error={exc}"
            ) from exc
