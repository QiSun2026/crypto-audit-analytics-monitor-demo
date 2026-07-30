# Evidence Integrity Harness

The harness is the domain-neutral evidence layer shared by the synthetic
commission and AI-agent action-log examples.

It provides:

- canonical JSON, SHA-256 hashing and stable identifiers;
- registered pre-commitment validation;
- evidence-pack artifact manifests and tamper checks;
- source-row lineage and append-only review-chain validation;
- bounded conclusion vocabulary and a required human decision boundary.

It does not provide:

- source authentication or an external timestamp;
- production enforcement or transaction blocking;
- legal, HR, fraud or misconduct conclusions;
- automated risk appetite, thresholds or human decisions.

## Release gates

The public package is releasable only when:

1. runtime evidence gates G1-G5 and G8 pass;
2. deterministic regeneration and review-chain tests pass;
3. the committed offline demos match a fresh render;
4. the fixed allowlist contains every released file and no prohibited path;
5. the generated release manifest binds every public artifact to SHA-256.

See [EVIDENCE_CONTRACT.md](EVIDENCE_CONTRACT.md) for the stable G1-G8
definitions and assurance levels.
