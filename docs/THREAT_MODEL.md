# ControlSub Threat Model

## Assets and trust boundaries

Protected assets: the owner-sealed security charter; candidate and assessment hashes; unaltered archived verdicts; the single currently eligible ratified substitution; downstream action eligibility. ControlSub holds **no GEN custody** and executes no external system changes.

Trust boundaries:
- The charter owner is trusted **to choose** security objectives, scope, the baseline, approved repositories, and to consent to a substitution. They are not trusted to bypass an actual semantic pass inside ControlSub.
- A proposer is untrusted. They can nominate alternative controls and allowed-repository revisions but cannot force acceptance or owner ratification.
- Published evidence is untrusted content, even when commit pinned. Only its precise bytes and declared repository affiliation are verified.
- The leader is untrusted; validators must independently retrieve and assess sources.
- Other contracts must independently pin the actual ControlSub address plus charter hash and certificate hash. A receipt without on-chain `is_active()` verification is inert.

## Attacks and mitigations

| Attack | ControlSub defence | Residual limitation |
| --- | --- | --- |
| Leader invents a COVERED dimension | Validator independently fetches source and recomputes complete typed outcome | Validators may share a model bias |
| Leader invents an evidence excerpt | Validator fetches immutable public bytes, never reads leader excerpt | Published evidence might itself be false |
| Proposer swaps source after assessment | 40-hex commit path, owner allowlist and exact SHA256 match | GitHub availability remains external |
| Proposal points at a moving `main` branch | Deterministic URL regex rejects it | Pinned Git commit could be malicious |
| Prompt injection inside configuration | Explicit untrusted-data instructions; validator independently runs reasoning | Prompt injection cannot be eliminated completely |
| Approving a different charter | All certificates bind exact charter hash | Owner can create a *different* permissive charter; consumers must pin charter |
| Model drops one required objective | Complete ordered dimension vector; missing fields reject | LLM may agree on an incorrect COVERED state |
| Partial control passes from a vague numeric score | No scores, every mandatory dimension must be COVERED | Quality of objective wording matters |
| Material new loophole | Explicit no-new-weakening flag; separate failure modes | Unforeseen loopholes may not be found |
| An approved source later disappears | Certificate snapshot stays until expiry/revocation | Source availability isn't continuously watched |
| Owner ratifies without independent consensus | Only ASSESS_PASS candidate, exact assessment hash | Owner controls ratification, as designed |
| Owner ratifies very stale result | 72h ratification bound and max 90-day certificate | Subsequent runtime changes are not continuously verified |
| A second ratification races the current head | Expected active certificate hash | Transaction ordering still matters |
| Replay of old certificate after replacement | Exactly one active candidate, supersession | Consumers must re-check at action time |
| Revocation bypass | `is_active()` returns false after revoke | Cannot cancel already-finalized external actions |
| Candidate expiry circumvented | Chain transaction timestamp, not local Python wall clock | On-chain time is approximate |
| Candidate creator spoofing / wallet replays | Sender bound in candidate hash; owner ratification checked | This registry is not an identity-verification service |
| Multiple controls inflate evidence | Unique source URLs, source indices checked | Distinct files may contain duplicate assertions |

## Explicit non-guarantees

This contract does **not** prove that a live production system enforces its published configuration, that a security control eliminates every threat, or that a cited repository is independent or authoritative in a legal sense. It produces an auditable **source-backed and owner-consented substitution certificate** for the chosen security dimensions. It does not control or reverse actions taken outside a consumer that actually enforces the on-chain predicate. In particular, it is not certification to ISO 27001, SOC 2, NIST, PCI DSS, or equivalent standards.

## Fail-closed behavior

Malformed or unavailable evidence prevents the assessment. A validator dissent prevents consensus. Complete assessments with `GAP` or `UNKNOWN` are recorded as non-passing. Only a fully covered vector plus no new material weakening may be ratified. Expiry, revocation, version replacement, wrong hashes, wrong contract address, or missing owner consent make the consumer predicate false.
