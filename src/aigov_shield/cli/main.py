"""Command-line interface for aigov-shield."""

from __future__ import annotations

import argparse
import json
import sys
from typing import Any


def cli(argv: list[str] | None = None) -> None:
    """Main CLI entry point for aigov-shield.

    Args:
        argv: Command-line arguments. Defaults to sys.argv[1:].
    """
    parser = argparse.ArgumentParser(
        prog="aigov-shield",
        description="AI governance infrastructure for regulated industries",
    )
    parser.add_argument(
        "--version",
        action="version",
        version=f"%(prog)s {_get_version()}",
    )

    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # Guard command
    guard_parser = subparsers.add_parser("guard", help="Run guards on text")
    guard_parser.add_argument("text", help="Text to check")
    guard_parser.add_argument(
        "--guards",
        default="pii,privilege,toxicity,injection",
        help="Comma-separated list of guards to run (default: pii,privilege,toxicity,injection)",
    )
    guard_parser.add_argument(
        "--action",
        choices=["block", "redact", "flag"],
        default="flag",
        help="Action on violation (default: flag)",
    )

    # Evaluate command
    eval_parser = subparsers.add_parser("evaluate", help="Evaluate a dataset")
    eval_parser.add_argument("--input", required=True, help="Input JSONL file")
    eval_parser.add_argument("--output", help="Output report file")
    eval_parser.add_argument(
        "--format",
        choices=["json", "html"],
        default="json",
        help="Output format (default: json)",
    )

    # Verify chain command
    verify_parser = subparsers.add_parser("verify-chain", help="Verify a chain of custody")
    verify_parser.add_argument("--input", required=True, help="Input JSONL chain file")

    # Report command
    report_parser = subparsers.add_parser("report", help="Generate NIST compliance report")
    report_parser.add_argument("--input", required=True, help="Input evaluation results JSON")
    report_parser.add_argument("--output", required=True, help="Output report file")
    report_parser.add_argument(
        "--format",
        choices=["json", "html"],
        default="html",
        help="Report format (default: html)",
    )

    args = parser.parse_args(argv)

    if args.command is None:
        parser.print_help()
        sys.exit(0)

    if args.command == "guard":
        _run_guard(args)
    elif args.command == "evaluate":
        _run_evaluate(args)
    elif args.command == "verify-chain":
        _run_verify_chain(args)
    elif args.command == "report":
        _run_report(args)


def _get_version() -> str:
    """Get the package version."""
    from aigov_shield._version import __version__

    return __version__


def _run_guard(args: argparse.Namespace) -> None:
    """Run guards on the provided text."""
    from aigov_shield.prevention.base import GuardAction

    action_map = {
        "block": GuardAction.BLOCK,
        "redact": GuardAction.REDACT,
        "flag": GuardAction.FLAG,
    }
    action = action_map[args.action]
    guard_names = [g.strip() for g in args.guards.split(",")]
    guards = _build_guards(guard_names, action)

    print(f"Running {len(guards)} guard(s) on input text...\n")

    all_passed = True
    for guard in guards:
        result = guard.check(args.text)
        status = "PASS" if result.passed else "FAIL"
        print(f"  [{status}] {result.guard_name} (confidence: {result.confidence:.2%})")
        if not result.passed:
            all_passed = False
            for v in result.violations:
                print(f"         - {v}")
        if result.modified_text and result.modified_text != args.text:
            print(f"         Modified: {result.modified_text[:200]}")

    print(f"\nOverall: {'PASS' if all_passed else 'FAIL'}")
    sys.exit(0 if all_passed else 1)


def _build_guards(names: list[str], action: Any) -> list:
    """Build guard instances from names."""
    from aigov_shield.prevention.pii_guard import PIIGuard
    from aigov_shield.prevention.privilege_guard import PrivilegeGuard
    from aigov_shield.prevention.prompt_injection_guard import PromptInjectionGuard
    from aigov_shield.prevention.topic_guard import TopicGuard
    from aigov_shield.prevention.toxicity_guard import ToxicityGuard

    guard_map = {
        "pii": PIIGuard,
        "privilege": PrivilegeGuard,
        "toxicity": ToxicityGuard,
        "injection": PromptInjectionGuard,
        "topic": TopicGuard,
    }

    guards = []
    for name in names:
        cls = guard_map.get(name)
        if cls is None:
            print(f"Warning: Unknown guard '{name}'. Available: {', '.join(guard_map)}")
            continue
        guards.append(cls(on_violation=action))
    return guards


def _run_evaluate(args: argparse.Namespace) -> None:
    """Run compliance evaluation on a dataset."""
    from aigov_shield.measurement.compliance_scorer import ComplianceScorer

    data = _load_jsonl(args.input)
    print(f"Loaded {len(data)} items from {args.input}")

    scorer = ComplianceScorer()
    results = scorer.evaluate(data)

    score = results.get("nist_compliance_score", 0)
    passed = results.get("overall_pass", False)
    print(f"\nNIST Compliance Score: {score:.1%} ({'PASS' if passed else 'FAIL'})")

    if args.output:
        if args.format == "html":
            from aigov_shield.reporting.nist_report import NISTComplianceReport

            report = NISTComplianceReport(results)
            report.save_html(args.output)
        else:
            with open(args.output, "w", encoding="utf-8") as f:
                json.dump(results, f, indent=2, default=str)
        print(f"Report saved to {args.output}")


def _run_verify_chain(args: argparse.Namespace) -> None:
    """Verify a chain of custody file."""
    from aigov_shield.accountability.chain_of_custody import ChainOfCustody, CustodyRecord

    chain = ChainOfCustody()
    data = _load_jsonl(args.input)

    for record_data in data:
        record = CustodyRecord(**record_data)
        chain._chain.append(record)

    valid, errors = chain.verify_chain()

    if valid:
        print(f"Chain verified: {len(chain)} records, all hashes valid.")
    else:
        print(f"Chain INVALID: {len(errors)} error(s) found:")
        for error in errors:
            print(f"  - {error}")

    sys.exit(0 if valid else 1)


def _run_report(args: argparse.Namespace) -> None:
    """Generate a NIST compliance report."""
    from aigov_shield.reporting.nist_report import NISTComplianceReport

    with open(args.input, encoding="utf-8") as f:
        results = json.load(f)

    report = NISTComplianceReport(results)

    if args.format == "html":
        report.save_html(args.output)
    else:
        report.save_json(args.output)

    print(f"Report saved to {args.output}")


def _load_jsonl(path: str) -> list:
    """Load a JSONL file into a list of dicts."""
    data = []
    with open(path, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                data.append(json.loads(line))
    return data


if __name__ == "__main__":
    cli()
