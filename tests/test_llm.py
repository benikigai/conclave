"""Regression tests for Conclave's provider-neutral LLM adapter."""

import os
import sys
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

SCRIPTS_DIR = Path(__file__).resolve().parents[1] / "scripts"
sys.path.insert(0, str(SCRIPTS_DIR))

import llm  # noqa: E402


class ProviderSelectionTests(unittest.TestCase):
    def test_provider_env_is_normalized(self):
        with patch.dict(os.environ, {"CONCLAVE_PROVIDER": " AnThRoPiC "}):
            self.assertEqual(llm._provider_from_env(), "anthropic")

    def test_invalid_provider_env_is_rejected(self):
        with patch.dict(os.environ, {"CONCLAVE_PROVIDER": "unknown"}):
            with self.assertRaisesRegex(ValueError, "Unsupported CONCLAVE_PROVIDER"):
                llm._provider_from_env()

    def test_provider_defaults_are_stable(self):
        with patch.dict(os.environ, {"CONCLAVE_MODEL": ""}):
            self.assertEqual(
                llm.model_for_provider("ollama"),
                "qwen3.8:27b-q8-64k",
            )
            self.assertEqual(
                llm.model_for_provider("anthropic"),
                "claude-sonnet-4-6",
            )

    def test_model_override_applies_explicitly(self):
        with patch.dict(os.environ, {"CONCLAVE_MODEL": "operator-model"}):
            self.assertEqual(llm.model_for_provider("ollama"), "operator-model")
            self.assertEqual(llm.model_for_provider("anthropic"), "operator-model")

    @patch("llm.anthropic.Anthropic")
    def test_ollama_client_uses_compatibility_endpoint(self, client_cls):
        expected = object()
        client_cls.return_value = expected

        result = llm.create_client("ollama")

        self.assertIs(result, expected)
        client_cls.assert_called_once_with(
            base_url=llm.OLLAMA_BASE_URL,
            api_key="ollama",
        )

    @patch("llm.anthropic.Anthropic")
    def test_anthropic_fallback_uses_native_client(self, client_cls):
        expected = object()
        client_cls.return_value = expected

        result = llm.create_client("anthropic")

        self.assertIs(result, expected)
        client_cls.assert_called_once_with()


class ResponseTextTests(unittest.TestCase):
    def test_thinking_blocks_are_ignored_and_text_is_joined(self):
        response = SimpleNamespace(
            content=[
                SimpleNamespace(type="thinking", thinking="hidden reasoning"),
                SimpleNamespace(type="text", text="first"),
                SimpleNamespace(type="text", text="second"),
            ]
        )

        self.assertEqual(llm.response_text(response), "first\nsecond")

    def test_missing_text_block_is_an_error(self):
        response = SimpleNamespace(
            content=[SimpleNamespace(type="thinking", thinking="hidden reasoning")]
        )

        with self.assertRaisesRegex(RuntimeError, "did not contain a text block"):
            llm.response_text(response)


if __name__ == "__main__":
    unittest.main()
