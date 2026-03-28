"""Tests for OpenAI wrapper."""

from __future__ import annotations

from unittest.mock import MagicMock

import pytest

from aigov_shield.integrations.openai_wrapper import GovernedChatCompletions
from aigov_shield.prevention import GuardAction, PIIGuard


def test_governed_chat_completions_blocks():
    mock_client = MagicMock()
    guard = PIIGuard(on_violation=GuardAction.BLOCK, confidence_threshold=0.0)
    wrapper = GovernedChatCompletions(client=mock_client, guards=[guard])
    with pytest.raises(ValueError, match="blocked the input"):
        wrapper.create(
            model="gpt-4",
            messages=[
                {"role": "user", "content": "My email is test@example.com and SSN 123-45-6789"},
            ],
        )


def test_governed_chat_completions_passes():
    mock_client = MagicMock()
    mock_response = MagicMock()
    mock_response.choices = [MagicMock()]
    mock_response.choices[0].message.content = "Hello there!"
    mock_client.chat.completions.create.return_value = mock_response

    guard = PIIGuard(on_violation=GuardAction.BLOCK)
    wrapper = GovernedChatCompletions(client=mock_client, guards=[guard])
    result = wrapper.create(
        model="gpt-4",
        messages=[{"role": "user", "content": "Hello world"}],
    )
    assert result is mock_response
    mock_client.chat.completions.create.assert_called_once()
