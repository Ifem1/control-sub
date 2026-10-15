# ControlSub Consensus Protocol

## Question

> Given a frozen security charter (baseline, context, objective/failure-mode dimensions), and one frozen bundle of alternative controls supported by the exact bytes of public commit-pinned source files, does that bundle establish **complete objective-by-objective coverage without introducing another material weakening**?

This is neither popularity scoring nor a general assurance engine. The contract assesses only the owner-declared scope and immutable public evidence. It does not authenticate the real-world operation of software or the correctness of an owner's charter.

## Two independent runs

`assess()` first requires the exact candidate hash, immutable charter hash, `SUBMITTED` state, and bounded parseable public sources. A `run_nondet_unsafe` boundary contains all nondeterministic work.

Leader:
1. Fetch each source from immutable `raw.githubusercontent.com` commit URLs.
2. Require UTF-8, 20–6000 bytes, source repo on the sealed allowlist, SHA256 exactly equal to the committed hash.
3. Supply **the full fetched source contents** plus charter and candidate to the LLM. All text is explicitly untrusted data.
4. Validate the complete normalized response: exact dimension order, `COVERED|GAP|UNKNOWN` on each, unique ascending source indices for COVERED, no indices otherwise, `YES|NO|UNKNOWN` weakening flag, reason from a closed enum.

Validator:
1. Reject non-Return leader results.
2. Validate leader output exactly as a typed complete value (not merely valid JSON).
3. Independently **re-fetch every source** and independently recompute SHA256 and read bounds. Validator does *not* consume leader-provided source bytes or summaries.
4. Independently execute the full assessment prompt using validator-fetched evidence.
5. Independently normalize and compare all decision-critical fields, **including the full per-dimension coverage vector, exact supporting source indices, weakening flag and reason code**. Any disagreement returns false.

The validator does not merely check the leader's format, or run a prompt asking whether the leader's opinion sounds plausible. The second classification is independently computed from source bytes. Both runs may agree on a mistake; this is a limitation of LLM consensus, not a formal proof.

## Deterministic post-consensus state

`ASSESS_FAIL` if *any* GAP or `no_new_material_weakening=NO`.

`ASSESS_UNKNOWN` if no hard fail and *any* UNKNOWN or weakening UNKNOWN.

`ASSESS_PASS` iff **every** frozen dimension is COVERED and weakening = YES.

Neither a failed nor unknown candidate may be ratified. Consensus by itself never approves a substitution: `ratify()` additionally requires the charter owner (bound to `gl.message.sender_address` at charter creation), exact assessment hash and exact active certificate precondition. An assessment older than 72 hours cannot be ratified. Ratification makes the preceding certificate `SUPERSEDED` and increments the version.

There is no ratification for an unassessed, malformed, or rejected candidate; no mutable rubric; no admin bypass. New source/evidence requires a new proposal and another consensus round.

## Source fingerprints and reproducibility

All content hashes use standard SHA256 of the exact UTF-8 byte sequences. All charter, candidate, assessment and certificate hashes use SHA256 of deterministic JSON (`json.dumps(sort_keys=True, separators=(',', ':'), ensure_ascii=True)`). Hashes bind all economic and permission-relevant context, not just a title. Sources are bounded and retrievable at immutable Git commit SHAs; a branch name is rejected even if it currently serves identical bytes.

A Git commit identifies a published source revision; it does not prove that the code is deployed, configured, enforced in production, written by a disinterested authority, or free of malicious configuration. Caller- and owner-provided statements remain untrusted.

## Why exact field comparison

Independent validators may choose different but valid evidence mappings, resulting in an undetermined transaction. That is deliberate for high-stakes control substitution: ambiguous or nonconvergent assessment must fail closed. A softer equivalence rule that only compared a global PASS bit could permit fabricated support mappings or hide a missed mandatory dimension.

## Security objective example

Hardware-bound authentication and an independent pre-activation review are mandatory. The model may not replace them with a compensating numeric score (e.g. "8/10 is sufficiently secure"). If the alternative has a password-only break-glass mode, even if its main path passes hardware authentication, validators are instructed to report a material weakening and the certificate cannot pass.
