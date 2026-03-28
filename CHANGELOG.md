# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.1.0] - 2026-03-28

### Added

- **Prevention Layer**: Runtime guardrails for AI outputs
  - `PrivilegeGuard`: Legal privilege detection (attorney-client, work product, settlement)
  - `PIIGuard`: PII detection and redaction (10 categories with 4 redaction modes)
  - `ToxicityGuard`: Toxicity and harmful content detection with ML classifier hook
  - `TopicGuard`: Topic enforcement and boundary detection
  - `PromptInjectionGuard`: Prompt injection attack detection
  - `GuardChain`: Compose multiple guards with fail-fast, run-all, and priority modes

- **Accountability Layer**: Evidence and audit trail infrastructure
  - `ChainOfCustody`: SHA-256 tamper-evident audit chain with verification
  - `EvidenceLogger`: Structured evidence logging for litigation support
  - `DocumentTracker`: Source document provenance tracking
  - `DecisionRecorder`: AI decision point recording with context manager support
  - Export utilities for JSON, JSONL, and CSV formats

- **Measurement Layer**: Compliance evaluation and scoring
  - `PIIEvaluator`: PII leakage rate measurement
  - `PrivilegeEvaluator`: Privilege disclosure rate measurement
  - `GroundingEvaluator`: Factual grounding and hallucination measurement
  - `BiasEvaluator`: Demographic bias measurement across 5 dimensions
  - `ComplianceScorer`: NIST AI RMF composite compliance scoring
  - `DriftMonitor`: Compliance drift detection between evaluation periods

- **Integrations**
  - LangChain callback handler (`GovernanceCallbackHandler`)
  - OpenAI API wrapper (`GovernedOpenAI`)
  - FastAPI middleware (`GovernanceMiddleware`)

- **Reporting**
  - NIST AI RMF compliance report generator (HTML and JSON output)
  - Guard results HTML report generator
  - Machine-readable JSON report generator

- **CLI**
  - `aigov-shield guard`: Run guards on text input
  - `aigov-shield evaluate`: Evaluate a JSONL dataset for compliance
  - `aigov-shield verify-chain`: Verify chain of custody integrity
  - `aigov-shield report`: Generate NIST compliance reports

- **Infrastructure**
  - Zero required dependencies for core functionality
  - Optional integrations via extras (langchain, openai, fastapi, reports)
  - Python 3.9, 3.10, 3.11, and 3.12 support
  - GitHub Actions CI/CD pipeline with lint, test, typecheck, and build stages
  - 140+ test cases across all modules
  - Apache 2.0 license

[0.1.0]: https://github.com/garyatwalAI/aigov-shield/releases/tag/v0.1.0
