# Crypto Audit Analytics Monitor

An Audit Assurance application built on the domain-neutral **RiskFirewall
Evidence Integrity Harness**.

**Working tagline:** Evidence-grade assurance for high-risk decisions.

`Firewall` refers to evidence-pack admission. Integrity drift fails closed
before export. The project does not block transactions, launches, employees or
AI agents.

## Offline bilingual demo

Open [demo/index.html](demo/index.html) directly after cloning. The landing page
offers two fabricated cases:

1. **Commission assurance:** full-population wallet and commission tests,
   bounded samples, false positives, lineage and worked human reviews.
2. **AI agent action assurance:** one deterministic rule checks whether an
   irreversible action binds to an exact, valid human approval payload.

The second case treats AI-agent activity as the audited subject. No model
performs detection, classification, threshold setting or decision-making.

To regenerate all three pages:

```powershell
$env:PYTHONPATH = "src"
python -m crypto_audit_monitor.run_demo
start demo\index.html
```

## Shared evidence contract

Both cases use the same domain-neutral mechanisms:

```text
Pre-commitment
  -> deterministic execution
  -> fail closed on drift
  -> traceable evidence pack
  -> accountable human decision
```

The [Evidence Contract](EVIDENCE_CONTRACT.md) defines Gate Profile v0.1 and
four cumulative, non-compensating assurance levels. Each evidence pack is an
L1 release candidate until G6 and G7 pass against the committed artifacts.
The repository demonstrates `L1_deterministic_recomputation` on fabricated
data only after that release harness passes. It does not authenticate real
sources or provide independent external assurance.

## What the commission case demonstrates

- two control objectives and three deterministic assertions;
- 500 fabricated employees, 2,000 affiliates and 12,000 commission payments;
- full-population testing and five pre-committed bounded samples;
- 13 assertion hits consolidated into 6 review cases plus 2 visible context
  items;
- seeded positive, negative and designed-false-positive controls;
- snapshot hashes, control totals, versioned SQL and exact source-row lineage;
- three worked review cases in an append-only, hash-chained record.

## What the agent-action case demonstrates

- one fabricated action table and one fabricated approval table;
- one versioned SQL rule;
- exact approval-payload hash binding;
- explicit missing, denied, mismatched and expired approval signals;
- reversible and correctly approved actions retained as visible context;
- no production enforcement and no automated conclusion;
- no test of approval uniqueness, revocation, consumption or one-time use;
- an initialized review chain with zero human records and no disposition.

## Safety boundary

This repository:

- contains fabricated identifiers and events only;
- does not prove fraud, misconduct, policy breach or control effectiveness;
- does not recommend a real organizational threshold;
- does not provide authentication, real-time monitoring or production access
  controls;
- does not make an HR, legal, payment, launch or blocking decision.

Do not submit real employee, affiliate, wallet, payment, agent-action or
investigation data.

## Repository map

```text
config/                 Registered audit and agent-action configurations
sql/                    Three deterministic SQL rules
src/crypto_audit_monitor/harness/
                        Domain-neutral evidence-integrity mechanisms
src/crypto_audit_monitor/
                        Two synthetic applications and renderers
tests/                  Deterministic and adversarial release checks
demo/                   Offline bilingual landing page and two cases
EVIDENCE_CONTRACT.md    Gate profile and assurance vocabulary
```

## Verification

```powershell
$env:PYTHONPATH = "src"
python -m pytest -q
```

GitHub Actions runs the same release harness on each push and pull request.

## License

Release 0.2.0 in this repository is provided under the
[Apache License 2.0](LICENSE). Earlier copies distributed under MIT remain
governed by their applicable MIT terms; this release does not revoke those
rights.

The license provides no warranty and does not validate this Prototype for real
employee monitoring, audit conclusions or automated decisions.
