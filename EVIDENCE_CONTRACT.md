# RiskFirewall Evidence Contract

Working tagline: **Evidence-grade assurance for high-risk decisions.**

`Firewall` describes the evidence boundary only. A failed integrity gate blocks
evidence-pack export. It does not block a transaction, launch, employee action
or AI-agent action.

## Reuse-oriented contract

The mechanisms are designed to be domain-neutral. The current release
demonstrates them only within one third-line Risk Control Assurance
application, using two synthetic case contexts. Cross-domain reuse has not
been independently exercised.

Any future application or domain reuse must preserve the same contract:

1. register the exact configuration and rule hashes before the logical run;
2. execute a deterministic test against a hash-bound snapshot;
3. fail closed when configuration, rule, data or lineage drifts;
4. preserve every review item with its rule, run, snapshot and source rows;
5. use bounded conclusions and keep accountable human authority explicit;
6. preserve later review corrections in a tamper-evident append-only chain.

The implementation designed for reuse is under
`src/crypto_audit_monitor/harness/`. In the current evidence base, domain data
generation, SQL routing, sampling and business interpretation all remain
within the same Risk Control Assurance application.

## Gate Profile v0.1

| Gate | Requirement | Runtime or release |
| --- | --- | --- |
| G1 | Snapshot integrity | Runtime |
| G2 | Population completeness | Runtime |
| G3 | Registered pre-commitment | Runtime |
| G4 | Rule validation | Runtime |
| G5 | Source-row traceability | Runtime |
| G6 | Append-only review contract | Release test |
| G7 | Deterministic recomputation | Release test |
| G8 | Bounded conclusions | Runtime |

This is a versioned project profile, not an industry standard. A gate may not be
offset by another gate. Any required failure keeps the evidence pack outside
the claimed assurance level.

## Assurance levels

| Level | Meaning |
| --- | --- |
| L0 declaration consistency | Declared claims are internally consistent |
| L1 deterministic recomputation | A reviewer can recompute results from bound inputs and rules |
| L2 source authenticated | Input provenance and issuer identity are authenticated |
| L3 external validation | An independent party validates the evidence and control operation |

Levels are cumulative and non-compensating. A project cannot skip a lower
level. Each generated evidence pack is labelled an L1 release candidate until
the repository release harness validates G6 and G7 against the committed
artifacts. The current synthetic repository demonstrates deterministic
recomputation after those tests pass. Neither case authenticates real sources
nor provides external assurance.

## Current case contexts within one application

- **Audit Assurance:** fabricated wallet and commission populations, two
  controls, full-population testing, explicit samples and human reviews.
- **AI agent action assurance:** one fabricated rule tests whether an
  irreversible action binds to the exact approved payload during its valid
  time window.

In the second case, the AI agent is the audited subject. No model performs
detection, classification, threshold setting, review disposition or final
decision. The example does not test approval uniqueness, revocation,
consumption or one-time use; those would require a separately pre-committed
control. These two case contexts do not independently demonstrate reuse in a
different assurance domain.
