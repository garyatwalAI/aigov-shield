"""Example: LangChain RAG pipeline with governance.

Demonstrates how to add governance to a LangChain retrieval-augmented
generation pipeline. Requires: pip install aigov-shield[langchain] langchain-openai

Note: Set the OPENAI_API_KEY environment variable before running.
"""

from __future__ import annotations

import os
import sys


def main() -> None:
    # Check for API key
    if not os.environ.get("OPENAI_API_KEY"):
        print("Set OPENAI_API_KEY environment variable to run this example.")
        print("Example: export OPENAI_API_KEY=sk-...")
        sys.exit(1)

    from aigov_shield.prevention import PIIGuard, PrivilegeGuard, GuardAction
    from aigov_shield.accountability import ChainOfCustody, EvidenceLogger
    from aigov_shield.integrations import GovernanceCallbackHandler

    # Set up governance
    evidence_logger = EvidenceLogger(case_id="RAG-DEMO-001")
    custody = ChainOfCustody()

    handler = GovernanceCallbackHandler(
        guards=[
            PIIGuard(on_violation=GuardAction.REDACT),
            PrivilegeGuard(on_violation=GuardAction.FLAG),
        ],
        evidence_logger=evidence_logger,
        chain_of_custody=custody,
    )

    # Use with LangChain
    from langchain_openai import ChatOpenAI

    llm = ChatOpenAI(model="gpt-4", callbacks=[handler])
    response = llm.invoke("What are the key principles of data governance?")

    print(f"Response: {response.content[:200]}...")
    print(f"Chain length: {len(custody)}")
    print(f"Evidence records: {len(evidence_logger.get_records())}")

    valid, _ = custody.verify_chain()
    print(f"Audit chain valid: {valid}")


if __name__ == "__main__":
    main()
