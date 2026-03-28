"""LangChain callback handler for automatic governance."""

from __future__ import annotations

import json
from typing import TYPE_CHECKING, Any

try:
    from langchain_core.callbacks import BaseCallbackHandler
except ImportError:
    # Create a stub base class when langchain is not installed
    class BaseCallbackHandler:  # type: ignore[no-redef]
        """Stub for when langchain-core is not installed."""

        pass


if TYPE_CHECKING:
    from aigov_shield.accountability.chain_of_custody import ChainOfCustody
    from aigov_shield.accountability.evidence_logger import EvidenceLogger
    from aigov_shield.prevention.base import BaseGuard, GuardResult


class GovernanceCallbackHandler(BaseCallbackHandler):
    """LangChain callback handler that applies governance to LLM calls.

    Automatically runs guards on inputs and outputs, logs evidence,
    and maintains chain of custody for every LLM interaction.

    Args:
        guards: List of guard instances to run on inputs and outputs.
        evidence_logger: Optional evidence logger for litigation support.
        chain_of_custody: Optional chain of custody for tamper-evident audit.
        check_inputs: Whether to run guards on LLM inputs.
        check_outputs: Whether to run guards on LLM outputs.

    Raises:
        ImportError: If langchain-core is not installed.

    Example:
        >>> from aigov_shield.integrations import GovernanceCallbackHandler
        >>> handler = GovernanceCallbackHandler(
        ...     guards=[PIIGuard(), PrivilegeGuard()],
        ...     evidence_logger=EvidenceLogger(case_id="CASE-001"),
        ... )
    """

    def __init__(
        self,
        guards: list[BaseGuard] | None = None,
        evidence_logger: EvidenceLogger | None = None,
        chain_of_custody: ChainOfCustody | None = None,
        check_inputs: bool = True,
        check_outputs: bool = True,
    ) -> None:
        super().__init__()
        self.guards = guards or []
        self.evidence_logger = evidence_logger
        self.chain_of_custody = chain_of_custody
        self.check_inputs = check_inputs
        self.check_outputs = check_outputs
        self._last_results: list[GuardResult] = []

    @property
    def last_results(self) -> list[GuardResult]:
        """Return results from the most recent guard checks."""
        return self._last_results

    def _run_guards(self, text: str) -> list[GuardResult]:
        """Run all guards against the given text."""
        results = []
        for guard in self.guards:
            result = guard.check(text)
            results.append(result)
        return results

    def on_llm_start(
        self,
        serialized: dict[str, Any],
        prompts: list[str],
        **kwargs: Any,
    ) -> None:
        """Run guards on LLM input prompts."""
        if not self.check_inputs:
            return

        for prompt in prompts:
            results = self._run_guards(prompt)
            self._last_results = results

            if self.chain_of_custody:
                guard_dicts = [
                    {"guard": r.guard_name, "passed": r.passed, "confidence": r.confidence}
                    for r in results
                ]
                self.chain_of_custody.add_record(
                    interaction_type="query",
                    content=prompt,
                    actor="langchain",
                    guard_results=guard_dicts,
                )

            if self.evidence_logger:
                self.evidence_logger.log_event(
                    event_type="llm_input",
                    description=f"LLM input checked by {len(self.guards)} guards",
                    metadata={
                        "prompt_length": len(prompt),
                        "guards_passed": all(r.passed for r in results),
                    },
                )

    def on_llm_end(self, response: Any, **kwargs: Any) -> None:
        """Run guards on LLM output."""
        if not self.check_outputs:
            return

        # Extract text from response - handle different response types
        output_text = ""
        if hasattr(response, "generations"):
            for gen_list in response.generations:
                for gen in gen_list:
                    if hasattr(gen, "text"):
                        output_text += gen.text
        elif isinstance(response, str):
            output_text = response

        if output_text:
            results = self._run_guards(output_text)
            self._last_results = results

            if self.chain_of_custody:
                guard_dicts = [
                    {"guard": r.guard_name, "passed": r.passed, "confidence": r.confidence}
                    for r in results
                ]
                self.chain_of_custody.add_record(
                    interaction_type="response",
                    content=output_text,
                    actor="langchain",
                    guard_results=guard_dicts,
                )

            if self.evidence_logger:
                self.evidence_logger.log_generation(
                    prompt="[from langchain callback]",
                    response=output_text,
                    model="unknown",
                    guard_results=[{"guard": r.guard_name, "passed": r.passed} for r in results],
                )

    def on_llm_error(self, error: BaseException, **kwargs: Any) -> None:
        """Log LLM errors."""
        if self.evidence_logger:
            self.evidence_logger.log_event(
                event_type="llm_error",
                description=str(error),
            )

    def on_chain_start(
        self,
        serialized: dict[str, Any],
        inputs: dict[str, Any],
        **kwargs: Any,
    ) -> None:
        """Log chain start for audit trail."""
        if self.chain_of_custody:
            self.chain_of_custody.add_record(
                interaction_type="query",
                content=json.dumps(inputs, default=str),
                actor="langchain_chain",
            )

    def on_chain_end(self, outputs: dict[str, Any], **kwargs: Any) -> None:
        """Log chain end for audit trail."""
        if self.chain_of_custody:
            self.chain_of_custody.add_record(
                interaction_type="response",
                content=json.dumps(outputs, default=str),
                actor="langchain_chain",
            )

    def on_tool_start(
        self,
        serialized: dict[str, Any],
        input_str: str,
        **kwargs: Any,
    ) -> None:
        """Log tool usage for audit trail."""
        if self.chain_of_custody:
            self.chain_of_custody.add_record(
                interaction_type="query",
                content=input_str,
                actor="langchain_tool",
                metadata={"tool": serialized.get("name", "unknown")},
            )

    def on_retriever_end(self, documents: Any, **kwargs: Any) -> None:
        """Log document retrieval for audit trail."""
        if self.evidence_logger:
            doc_ids = []
            for doc in documents:
                doc_id = getattr(doc, "metadata", {}).get("source", str(doc)[:100])
                doc_ids.append(str(doc_id))
            self.evidence_logger.log_retrieval(
                query="[from langchain retriever]",
                documents_retrieved=doc_ids,
                retrieval_method="langchain_retriever",
            )
