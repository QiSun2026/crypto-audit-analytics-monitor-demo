# RiskFirewall AI — Risk Control Assurance

**Transactions, Processes & AI Actions · Third Line**

## RiskFirewall AI family

RiskFirewall AI is a portfolio family built around one governance method, not
one shared runtime:

`Declared boundary → constrained or deterministic execution → fail-closed evidence gate → traceable review package → accountable human decision`

It governs whether evidence may advance to accountable human review. It does
not approve, reject, execute, deploy or certify the underlying product, model,
transaction or control.

| Project | Control object | Role |
| --- | --- | --- |
| **[Product Risk Review](https://github.com/QiSun2026/product-risk-review-skill)** | Complex investment products and their claims | Second-line evidence review |
| **[Model Risk Review](https://github.com/QiSun2026/riskfirewall-model-risk-review)** | Models and AI decision systems | Developer-built, second-line-style review |
| **[Risk Control Assurance](https://github.com/QiSun2026/crypto-audit-analytics-monitor-demo)** | Transactions, processes and AI actions | Third-line assurance prototype |

The repositories share this method and human-authority boundary. They do not
claim a common engine, common data model or production deployment.

A third-line, evidence-bound assurance Prototype built on the **RiskFirewall
Evidence Integrity Harness**. The Harness is designed for domain-neutral
reuse, but this release demonstrates it only within one Risk Control Assurance
application; cross-domain reuse has not been independently exercised.

`Firewall` refers only to evidence-pack admission: integrity drift stops
evidence export. It does not block transactions, launches, employees or agent
actions. `RiskFirewall AI` names the audited AI-action domain and an
agent-ready target workflow; this verified release does not use a live AI or
Agent to execute tests or make decisions.

## Five-minute bilingual Demo

Open [demo/index.html](demo/index.html) directly after cloning. The landing page
explains one product, two synthetic assurance cases and one controlled workflow
view:

1. **Wallet and commission review:** full-population tests, bounded samples,
   false positives, lineage and worked human-review fixtures.
2. **AI action approval review:** deterministic testing of whether an
   irreversible action binds to the exact, valid human approval payload.
3. **Controlled workflow view of Case 1:** a frozen human mandate, allowlisted
   execution, source-cited deterministic drafting, human-only dispositions and
   an unsigned conclusion draft. This is not a third case.

To regenerate all four pages:

```powershell
$env:PYTHONPATH = "src"
python -m crypto_audit_monitor.run_demo
start demo\index.html
```

```bash
PYTHONPATH=src python -m crypto_audit_monitor.run_demo
open demo/index.html       # macOS
xdg-open demo/index.html   # Linux
```

## Contribution boundary

The Owner set the objective, risk boundaries and release authorization. Codex
performed implementation, testing, documentation and Git delivery. This
development contribution model does not change the product boundary:
accountable humans retain exception decisions and any assurance conclusion.

## Shared evidence contract

```text
Pre-commitment
  -> deterministic execution
  -> fail closed on drift
  -> traceable evidence pack
  -> accountable human decision
```

The [Evidence Contract](EVIDENCE_CONTRACT.md) defines Gate Profile v0.1 and
four cumulative, non-compensating assurance levels. The release harness
demonstrates `L1_deterministic_recomputation` on fabricated, hash-bound inputs.
It does not authenticate real sources or provide independent external
validation.

## What the commission case demonstrates

- two control objectives and three deterministic assertions;
- 500 fabricated employees, 2,000 affiliates and 12,000 commission payments;
- full-population testing and five pre-committed bounded samples;
- 13 assertion hits consolidated into 6 review cases plus 2 visible context
  items;
- seeded positive, negative and designed-false-positive controls;
- snapshot hashes, control totals, versioned SQL and exact source-row lineage;
- four append-only, hash-chained review records across three worked cases,
  including one correction that preserves the superseded record.

## What the AI-action case demonstrates

- one fabricated action table and one fabricated approval table;
- one versioned SQL rule and exact approval-payload hash binding;
- explicit missing, denied, mismatched and expired approval signals;
- reversible and correctly approved actions retained as visible context;
- no production enforcement and no automated conclusion;
- no test of approval uniqueness, revocation, consumption or one-time use;
- an initialized review chain with zero human records and no disposition.

AI-agent activity is the audited subject. No model performs detection,
classification, threshold setting or decision-making.

## What the bounded workflow demonstrates

The [Bounded Agentic Workflow](BOUNDED_AGENTIC_WORKFLOW.md) is a deterministic
control-plane simulation on the commission case:

- a human-authored mandate binds scope, thresholds and prohibitions;
- an exact plan is frozen before one allowlisted deterministic test runs;
- a deterministic fixture drafts source-cited explanations and questions;
- raw fixture inputs and outputs remain replayable and hash-bound;
- append-only human-review fixtures are the only source of dispositions;
- the resulting conclusion remains an unsigned, bounded draft.

The fixture proves the workflow controls and replay contract. It does not
establish external Agent execution, model performance or autonomous auditing.

## Safety boundary

This repository:

- contains fabricated identifiers and events only;
- does not prove fraud, misconduct, policy breach or control effectiveness;
- does not recommend a real organizational threshold;
- does not provide authentication, real-time monitoring or production access
  controls;
- does not make an HR, legal, payment, launch or blocking decision;
- does not sign an audit opinion or assurance conclusion.

Do not submit real employee, affiliate, wallet, payment, agent-action or
investigation data.

## Repository map

```text
config/                 Registered audit and agent-action configurations
sql/                    Three deterministic SQL rules
src/crypto_audit_monitor/harness/
                        Evidence-integrity mechanisms designed for reuse
src/crypto_audit_monitor/
                        Synthetic cases, bounded workflow and renderers
tests/                  Deterministic and adversarial release checks
demo/                   Offline bilingual landing page and case views
EVIDENCE_CONTRACT.md    Gate profile and assurance vocabulary
BOUNDED_AGENTIC_WORKFLOW.md
                        Human/automation authority boundary
REVIEW_SCOPE.md         Exact release-review and version boundary
```

## Verification

```powershell
$env:PYTHONPATH = "src"
python -m pytest -q
```

GitHub Actions runs the same released test suite on each push and pull request.

The current released suite passes 82 deterministic and adversarial checks.
This is engineering verification, not evidence of adoption, model accuracy or
real-world control effectiveness.

## Status

Public release `v0.3.0` remains the current functional release. The current
`main` documentation aligns the repository with the RiskFirewall AI family
contract; it does not rewrite the immutable `v0.3.0` release artifact or alter
the deterministic assurance logic.

## License

Release 0.3.0 is provided under the [Apache License 2.0](LICENSE). Earlier
copies distributed under MIT remain governed by their applicable MIT terms;
this release does not revoke those rights.

The license provides no warranty and does not validate this Prototype for real
employee monitoring, audit conclusions or automated decisions.
