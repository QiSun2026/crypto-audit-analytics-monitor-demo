# RiskFirewall Evidence Integrity Harness

The Harness is designed for domain-neutral reuse. This release demonstrates it
only within one Risk Control Assurance application, through the synthetic
commission case, AI-action case and bounded workflow view. Cross-domain reuse
has not been independently exercised.

It provides:

- canonical JSON, SHA-256 hashing and stable identifiers;
- registered pre-commitment and exact plan-freeze validation;
- allowlisted deterministic execution;
- evidence-pack artifact manifests and tamper checks;
- source-row lineage and append-only review-chain validation;
- replay-bound deterministic drafting fixtures;
- bounded conclusion vocabulary and a required human decision boundary.

It does not provide:

- source authentication or an external timestamp;
- production enforcement or transaction blocking;
- legal, HR, fraud, AML or misconduct conclusions;
- automated risk appetite, thresholds, exception closure or signatures;
- live AI/Agent execution or model-performance evidence.

## Release gates

The Public package is releasable only when:

1. runtime evidence gates G1-G5 and G8 pass;
2. deterministic regeneration and review-chain tests pass;
3. plan, provider, citation, disposition and conclusion bypass tests pass;
4. the committed offline Demos match fresh renders;
5. the fixed allowlist contains every released file and no prohibited path;
6. the generated release manifest binds every allowlisted payload file to
   SHA-256, while the committed Git revision binds the manifest itself.

See [EVIDENCE_CONTRACT.md](EVIDENCE_CONTRACT.md) for stable G1-G8 definitions
and [BOUNDED_AGENTIC_WORKFLOW.md](BOUNDED_AGENTIC_WORKFLOW.md) for the
human/automation authority boundary.
