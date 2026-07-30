# RiskFirewall AI — Risk Control Assurance · Lean MVP Spec

The original audit application contract below remains frozen. Version 3 added
the domain-neutral mechanisms defined in `EVIDENCE_CONTRACT.md`, one synthetic
AI-agent action-log proof and one two-case offline showcase. Version 0.3 adds
one bounded agentic workflow proof on the existing commission case. It does not
add another commission control, a third domain or a production platform.

## Authorized v0.3 workflow increment

`Human Audit Mandate -> Planning proposal -> Human freeze -> Allowlisted
deterministic test -> Source-cited investigation draft -> Human exception
records -> Unsigned bounded conclusion draft`.

- The human mandate owns scope, provisional thresholds, test allowlist and
  prohibitions.
- The plan has no execution authority until the exact hash is frozen.
- The deterministic workflow can invoke only
  `commission_full_population_v4`.
- Drafted claims, questions and unknowns must cite source rows already bound to
  the exception.
- Provider output cannot change status, thresholds, dispositions, conclusions
  or signatures.
- Validated fixture exchanges are hash-bound to their resulting drafts and
  retained for replay.
- Human review records remain the only source of exception dispositions.
- The conclusion is an unsigned draft based on human records only.
- v0.3 uses a deterministic fixture provider; no external model or Agent
  executor is called.

## Purpose

Demonstrate full-population Internal Audit analytics on fabricated data. The
system turns deterministic SQL signals into traceable exceptions for human
review. It does not determine misconduct, set company policy, or take action.

## Frozen implementation contract

- Two control objectives.
- Two versioned SQL rules with three assertions: A, B1 and B2.
- Five synthetic business tables only.
- One pre-committed rule configuration.
- One population run and five pre-committed bounded samples.
- JSON, CSV and self-contained bilingual HTML output.
- Human review fields are self-attested prototype records; no authentication.
- No LLM in detection, classification, conclusion or rationale.

## Business tables

| Table | Minimum fields |
| --- | --- |
| `employee` | `employee_id`, `has_affiliate_program_access` |
| `affiliate` | `affiliate_id`, `status` |
| `payout_wallet` | `wallet_id`, `address_hash`, `wallet_type` |
| `entity_wallet_link` | `link_id`, `entity_type`, `entity_id`, `wallet_id`, `valid_from`, `valid_to` |
| `commission_payment` | `payment_id`, `affiliate_id`, `accrual_period`, `amount_minor`, `payment_date`, `source_ref`, `payment_status` |

Names, emails, IPs, devices, geolocation, KYC, salary and real wallet
addresses are prohibited.

## Control objectives and assertions

### CO-01 — Beneficiary relationship integrity

Shared beneficiary-wallet relationships are identified and explained where
different entities are simultaneously linked to the same wallet.

- **A:** Overlapping links to one wallet across multiple entities.
- Self-custody overlap is `potential_exception`.
- Exchange-deposit or internal-treasury sharing is retained as
  `expected_shared`, never silently excluded.
- A non-overlapping link is a negative control, not an alert.

Human question: Is this a custody/collection address, or does it represent an
unexplained shared beneficiary relationship during the overlapping period?

### CO-02 — Commission payment integrity

Commission entitlements are paid once and are not split to avoid the
provisional review threshold.

- **B1:** the same source reference appears in multiple completed payments,
  including across affiliates, or the same affiliate, accrual period and amount
  repeats; a reversal pair is not an exception.
- **B2:** for one affiliate and accrual period, at least two completed payments
  fall within the configured inclusive window, each is below the configured
  threshold, and the combined amount meets or exceeds it.

Human question: Do the payments settle one entitlement, and if separate, is
there documented authorization explaining why each falls below the review
threshold?

## Pre-commitment

`config/rule_precommitment.json` owns:

- rule version IDs and SQL hashes;
- pipeline version for queue and evidence semantics;
- provisional synthetic threshold and inclusive day window;
- sample method, unit, size and seeds;
- timestamp that must precede each run.

A change creates a new version. Existing run artifacts are not overwritten.

## Population and sample

The population is bound by per-table row counts, hashes and control totals. A
sample selects affiliates by simple random sampling without replacement, using
five fixed seeds and a fixed size. All payments and wallet relationships for
selected affiliates are included; employee links to their wallets are retained.

Only observed results are reported. No probability, confidence, recall or
generalization to real populations is claimed.

## Blocking gates

1. **Snapshot integrity:** source hashes match the manifest.
2. **Population completeness:** row counts and control totals reconcile.
3. **Pre-commitment:** rule configuration predates the run and hashes resolve.
4. **Rule validation:** all seeded positive controls hit and all negative
   controls remain non-exceptions.
5. **Traceability:** every exception resolves to existing source row IDs.
6. **Append-only review:** corrections supersede; they do not overwrite.
7. **Determinism:** identical input/configuration reproduces the same exception
   set.
8. **Bounded conclusions:** each objective is exactly one of
   `no_exceptions_detected`, `exceptions_identified`, or `not_testable`.
   The rules never declare a control `effective`.

Failure of gates 1–5 or 7 blocks evidence-pack export. Gate 6 is demonstrated
by the review-log contract. Gate 8 blocks the summary.

## Human authority

Signals use neutral wording: `exception requiring explanation`. The Prototype
does not call a person fraudulent, determine control effectiveness after human
evidence, make an HR/legal decision, or authorize a payment or block.
