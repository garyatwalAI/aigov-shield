"""OpenAI API wrapper with governance controls."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from aigov_shield.prevention.base import BaseGuard, GuardAction, GuardResult

if TYPE_CHECKING:
    from aigov_shield.accountability.chain_of_custody import ChainOfCustody
    from aigov_shield.accountability.evidence_logger import EvidenceLogger


class GovernedChatCompletions:
    """Governed wrapper for chat completions.

    Intercepts chat completion requests to run guards on input messages
    and output responses, maintaining audit trails.

    Args:
        client: The underlying OpenAI client.
        guards: List of guards to apply.
        custody: Optional chain of custody.
        evidence_logger: Optional evidence logger.
    """

    def __init__(
        self,
        client: Any,
        guards: list[BaseGuard],
        custody: ChainOfCustody | None = None,
        evidence_logger: EvidenceLogger | None = None,
    ) -> None:
        self._client = client
        self._guards = guards
        self._custody = custody
        self._evidence_logger = evidence_logger
        self._last_results: list[GuardResult] = []

    @property
    def last_results(self) -> list[GuardResult]:
        """Return results from the most recent guard checks."""
        return self._last_results

    def create(self, **kwargs: Any) -> Any:
        """Create a chat completion with governance checks.

        Runs guards on input messages before sending to the API,
        and on the response after receiving it. Logs all interactions
        to the evidence logger and chain of custody if configured.

        Args:
            **kwargs: Arguments passed to the OpenAI chat completions API.

        Returns:
            The OpenAI chat completion response.

        Raises:
            ValueError: If a guard blocks the input.
        """
        messages = kwargs.get("messages", [])
        model = kwargs.get("model", "unknown")

        # Check input messages
        input_text = " ".join(
            msg.get("content", "") for msg in messages if isinstance(msg.get("content"), str)
        )

        input_results = []
        for guard in self._guards:
            result = guard.check(input_text)
            input_results.append(result)
            if not result.passed and result.action_taken == GuardAction.BLOCK:
                self._last_results = input_results
                raise ValueError(
                    f"Guard '{result.guard_name}' blocked the input: "
                    f"{len(result.violations)} violation(s) detected"
                )

        # Log input to custody chain
        if self._custody:
            self._custody.add_record(
                interaction_type="query",
                content=input_text,
                actor="openai_wrapper",
                model_id=model,
                guard_results=[
                    {"guard": r.guard_name, "passed": r.passed, "confidence": r.confidence}
                    for r in input_results
                ],
            )

        # Make the API call
        response = self._client.chat.completions.create(**kwargs)

        # Check output
        output_text = ""
        if hasattr(response, "choices") and response.choices:
            choice = response.choices[0]
            if hasattr(choice, "message") and hasattr(choice.message, "content"):
                output_text = choice.message.content or ""

        output_results = []
        if output_text:
            for guard in self._guards:
                result = guard.check(output_text)
                output_results.append(result)

        self._last_results = output_results or input_results

        # Log output to custody chain
        if self._custody:
            self._custody.add_record(
                interaction_type="response",
                content=output_text,
                actor="openai_wrapper",
                model_id=model,
                input_hash=None,
                guard_results=[
                    {"guard": r.guard_name, "passed": r.passed, "confidence": r.confidence}
                    for r in output_results
                ],
            )

        # Log to evidence logger
        if self._evidence_logger:
            self._evidence_logger.log_generation(
                prompt=input_text,
                response=output_text,
                model=model,
                guard_results=[
                    {"guard": r.guard_name, "passed": r.passed} for r in output_results
                ],
            )

        return response


class GovernedOpenAI:
    """Drop-in wrapper for the OpenAI client with governance.

    Wraps the OpenAI client to automatically apply guards, maintain
    chain of custody, and log evidence for every API call.

    Args:
        api_key: OpenAI API key.
        guards: List of guards to apply to all interactions.
        custody: Optional chain of custody for audit trails.
        evidence_logger: Optional evidence logger.
        **client_kwargs: Additional arguments passed to the OpenAI client constructor.

    Example:
        >>> client = GovernedOpenAI(
        ...     api_key="sk-...",
        ...     guards=[PIIGuard(), PrivilegeGuard()],
        ...     custody=ChainOfCustody(),
        ... )
        >>> response = client.chat.completions.create(
        ...     model="gpt-4",
        ...     messages=[{"role": "user", "content": "Hello"}],
        ... )
    """

    def __init__(
        self,
        api_key: str | None = None,
        guards: list[BaseGuard] | None = None,
        custody: ChainOfCustody | None = None,
        evidence_logger: EvidenceLogger | None = None,
        **client_kwargs: Any,
    ) -> None:
        try:
            from openai import OpenAI
        except ImportError as e:
            raise ImportError(
                "The 'openai' package is required for GovernedOpenAI. "
                "Install it with: pip install aigov-shield[openai]"
            ) from e

        self._client = OpenAI(api_key=api_key, **client_kwargs)
        self._guards = guards or []
        self._custody = custody
        self._evidence_logger = evidence_logger
        self.chat = _ChatNamespace(
            GovernedChatCompletions(
                client=self._client,
                guards=self._guards,
                custody=self._custody,
                evidence_logger=self._evidence_logger,
            )
        )


class _ChatNamespace:
    """Namespace to mirror OpenAI's client.chat.completions structure."""

    def __init__(self, completions: GovernedChatCompletions) -> None:
        self.completions = completions
