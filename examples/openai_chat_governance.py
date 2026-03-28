"""Example: OpenAI chat with governance controls.

Demonstrates the GovernedOpenAI wrapper that adds governance to every
OpenAI API call. Requires: pip install aigov-shield[openai]

Note: Set the OPENAI_API_KEY environment variable before running.
"""

from __future__ import annotations

import os
import sys


def main() -> None:
    if not os.environ.get("OPENAI_API_KEY"):
        print("Set OPENAI_API_KEY environment variable to run this example.")
        sys.exit(1)

    from aigov_shield.prevention import PIIGuard, PrivilegeGuard, ToxicityGuard, GuardAction
    from aigov_shield.accountability import ChainOfCustody
    from aigov_shield.integrations import GovernedOpenAI

    client = GovernedOpenAI(
        guards=[
            PIIGuard(on_violation=GuardAction.REDACT),
            PrivilegeGuard(on_violation=GuardAction.BLOCK),
            ToxicityGuard(on_violation=GuardAction.BLOCK),
        ],
        custody=ChainOfCustody(),
    )

    response = client.chat.completions.create(
        model="gpt-4",
        messages=[
            {"role": "system", "content": "You are a helpful insurance advisor."},
            {"role": "user", "content": "What does my flood insurance policy cover?"},
        ],
    )

    print(f"Response: {response.choices[0].message.content}")
    print(f"Guard results: {len(client.chat.completions.last_results)} checks performed")


if __name__ == "__main__":
    main()
