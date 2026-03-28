"""Performance benchmarks for prevention guards.

Measures execution time of each guard across various input sizes
to ensure they meet latency requirements (< 100ms for pattern-based guards).
"""

from __future__ import annotations

import statistics
import time

from aigov_shield.prevention import (
    GuardAction,
    GuardChain,
    PIIGuard,
    PrivilegeGuard,
    PromptInjectionGuard,
    TopicGuard,
    ToxicityGuard,
)


def benchmark_guard(guard_name: str, guard: object, texts: list[str], iterations: int = 100) -> dict:
    """Benchmark a single guard across multiple texts.

    Args:
        guard_name: Name for display.
        guard: Guard instance with a check() method.
        texts: List of texts to check.
        iterations: Number of iterations per text.

    Returns:
        Dictionary with timing statistics.
    """
    times: list[float] = []

    for text in texts:
        for _ in range(iterations):
            start = time.perf_counter()
            guard.check(text)  # type: ignore[union-attr]
            elapsed = (time.perf_counter() - start) * 1000
            times.append(elapsed)

    return {
        "guard": guard_name,
        "mean_ms": statistics.mean(times),
        "median_ms": statistics.median(times),
        "p95_ms": sorted(times)[int(len(times) * 0.95)],
        "p99_ms": sorted(times)[int(len(times) * 0.99)],
        "min_ms": min(times),
        "max_ms": max(times),
        "iterations": len(times),
    }


def main() -> None:
    # Test texts of varying sizes
    short_text = "Hello, this is a simple test message."
    medium_text = "The quarterly report shows significant growth. " * 20
    long_text = "This is a comprehensive analysis of the market conditions. " * 200

    texts = [short_text, medium_text, long_text]
    text_labels = ["short (~35 chars)", "medium (~900 chars)", f"long (~{len(long_text)} chars)"]

    guards = [
        ("PIIGuard", PIIGuard(on_violation=GuardAction.FLAG)),
        ("PrivilegeGuard", PrivilegeGuard(on_violation=GuardAction.FLAG)),
        ("ToxicityGuard", ToxicityGuard(on_violation=GuardAction.FLAG)),
        ("TopicGuard", TopicGuard(on_violation=GuardAction.FLAG)),
        ("PromptInjectionGuard", PromptInjectionGuard(on_violation=GuardAction.FLAG)),
    ]

    print("aigov-shield Guard Performance Benchmarks")
    print("=" * 70)
    print(f"Input sizes: {', '.join(text_labels)}")
    print(f"Iterations per text: 100")
    print()

    print(f"{'Guard':<25} {'Mean':>8} {'Median':>8} {'P95':>8} {'P99':>8} {'Max':>8}")
    print("-" * 70)

    all_pass = True
    for name, guard in guards:
        result = benchmark_guard(name, guard, texts, iterations=100)
        print(
            f"{result['guard']:<25} "
            f"{result['mean_ms']:>7.3f}ms "
            f"{result['median_ms']:>7.3f}ms "
            f"{result['p95_ms']:>7.3f}ms "
            f"{result['p99_ms']:>7.3f}ms "
            f"{result['max_ms']:>7.3f}ms"
        )
        if result["p95_ms"] > 100:
            print(f"  WARNING: P95 exceeds 100ms target!")
            all_pass = False

    # Benchmark guard chain
    print()
    print("Guard Chain (all guards combined):")
    print("-" * 70)

    chain = GuardChain([g for _, g in guards])
    chain_times: list[float] = []

    for text in texts:
        for _ in range(100):
            start = time.perf_counter()
            chain.run(text)
            elapsed = (time.perf_counter() - start) * 1000
            chain_times.append(elapsed)

    print(
        f"{'GuardChain (5 guards)':<25} "
        f"{statistics.mean(chain_times):>7.3f}ms "
        f"{statistics.median(chain_times):>7.3f}ms "
        f"{sorted(chain_times)[int(len(chain_times) * 0.95)]:>7.3f}ms "
        f"{sorted(chain_times)[int(len(chain_times) * 0.99)]:>7.3f}ms "
        f"{max(chain_times):>7.3f}ms"
    )

    print()
    if all_pass:
        print("All guards meet the < 100ms P95 latency target.")
    else:
        print("Some guards exceed the 100ms P95 target. Review implementation.")


if __name__ == "__main__":
    main()
