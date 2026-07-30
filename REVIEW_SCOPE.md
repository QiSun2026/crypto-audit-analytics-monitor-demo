# Release review scope

This file defines the review target for **RiskFirewall AI — Risk Control
Assurance** release 0.3.0.

## Exact target

- Review the committed Public repository revision, not a working directory.
- `RELEASE_MANIFEST.json` records the exact Private source commit and SHA-256
  hash of every allowlisted payload file. The committed Git revision binds the
  release manifest itself.
- The fixed Public allowlist excludes Private history, project records,
  reviewer conversations, non-release runtime output directories and real
  data. Committed synthetic Demo fixtures remain within the release boundary.

## Version boundary

- The previous Public line was release 0.2.0 at commit
  `bc5c494d89c2f006361b66552be805030a8a8a7a`.
- Its manifest recorded Private source commit
  `b4002dadc26592d376903da2de3c8268d594f564`.
- Release 0.3.0 is a new candidate generated from the Private source commit
  recorded in its own `RELEASE_MANIFEST.json`; it must not be inferred from
  the previous mapping.

## Claims in scope

The candidate may be reviewed for deterministic recomputation, evidence
bindings, release reproducibility, bilingual Demo consistency and the bounded
workflow controls implemented in the released files.

It does not claim authenticated real-world sources, external validation,
production enforcement, a live AI or Agent executor, autonomous audit
judgment, or a signed assurance conclusion. Internal red-team records are not
released and are not presented as independent external validation.
