"""Offline deterministic state machine and substantive validator adversarial checks."""
import hashlib
import json
import pytest
from fixtures import charter, controls, passing, missing, ambiguous, SOURCES, ROUTE


def setup(env):
    cs = env.contract
    ident = cs.create_charter(**charter())
    root = cs.get_charter(ident)["charter_hash"]
    candidate_id = cs.propose(ident,"Gateway+review controls",controls(),root)
    fingerprint = cs.get_candidate(candidate_id)["candidate_hash"]
    env.nondet.files = {ROUTE+"gateway.yml": SOURCES[0], ROUTE+"review.yml": SOURCES[1]}
    env.nondet.leader = passing()
    return ident, candidate_id, fingerprint


def approve(env):
    ident, candidate_id, fingerprint = setup(env)
    assert env.contract.assess(candidate_id,fingerprint) == env.mod.ASSESS_PASS
    h = env.contract.get_candidate(candidate_id)["assessment_hash"]
    receipt = env.contract.ratify(candidate_id,h,"")
    return ident, candidate_id, receipt


def test_pass_lifecycle(env):
    ident, candidate_id, receipt = approve(env)
    assert env.contract.is_active(ident,candidate_id,receipt,env.contract.get_charter(ident)["charter_hash"])
    assert env.contract.get_certificate(candidate_id)["is_current"]
    assert len(env.nondet.fetch_calls) == 4
    assert len(env.nondet.calls) == 2
    assert "INDEPENDENT VALIDATOR" in env.nondet.calls[1]


def test_malicious_leader_substantive_disagreement(env):
    _, candidate_id, fingerprint = setup(env)
    env.nondet.validator = missing()
    with pytest.raises(env.vm.UserError,match="CONSENSUS REJECTED"):
        env.contract.assess(candidate_id,fingerprint)
    assert not env.vm.agree
    assert env.contract.get_candidate(candidate_id)["status"] == env.mod.SUBMITTED


def test_malicious_leader_no_weakening_disagreement(env):
    _, candidate_id, fingerprint = setup(env)
    own = passing(); own["no_new_material_weakening"] = "NO"; own["reason_code"] = "PRIVILEGE_EXPANSION"
    env.nondet.validator = own
    with pytest.raises(env.vm.UserError): env.contract.assess(candidate_id,fingerprint)
    assert env.contract.get_candidate(candidate_id)["status"] == env.mod.SUBMITTED


def test_missing_dimension_is_not_pass(env):
    _, cid, fp = setup(env)
    env.nondet.leader = missing()
    assert env.contract.assess(cid,fp) == env.mod.ASSESS_FAIL
    assert env.contract.get_candidate(cid)["status"] == env.mod.ASSESS_FAIL
    with pytest.raises(env.vm.UserError): env.contract.ratify(cid,env.contract.get_candidate(cid)["assessment_hash"],"")


def test_unknown_is_not_pass(env):
    _, cid, fp = setup(env)
    env.nondet.leader = ambiguous()
    assert env.contract.assess(cid,fp) == env.mod.ASSESS_UNKNOWN


def test_owner_cannot_bypass_assessment(env):
    _, cid, _ = setup(env)
    with pytest.raises(env.vm.UserError,match="independently validated"):
        env.contract.ratify(cid,"","")


def test_non_owner_cannot_ratify(env):
    _, cid, fp = setup(env)
    env.contract.assess(cid,fp)
    env.gl.message.sender_address = env.B
    with pytest.raises(env.vm.UserError,match="only charter owner"):
        env.contract.ratify(cid,env.contract.get_candidate(cid)["assessment_hash"],"")


def test_source_revision_hash_is_mandatory(env):
    _, cid, fp = setup(env)
    env.nondet.files[ROUTE+"gateway.yml"] = b"tampered configuration"*10
    with pytest.raises(env.vm.UserError,match="source digest mismatch"):
        env.contract.assess(cid,fp)
    assert env.contract.get_candidate(cid)["status"] == env.mod.SUBMITTED


def test_source_unavailable_is_not_treated_as_pass(env):
    _, cid, fp = setup(env)
    del env.nondet.files[ROUTE+"review.yml"]
    with pytest.raises(Exception): env.contract.assess(cid,fp)
    assert env.contract.get_candidate(cid)["status"] == env.mod.SUBMITTED


def test_empty_or_oversized_evidence_rejected(env):
    _, cid, fp = setup(env)
    for replacement in (b"", b"x"*6001):
        env.nondet.files[ROUTE+"gateway.yml"] = replacement
        with pytest.raises(env.vm.UserError): env.contract.assess(cid,fp)


def test_wrong_charter_hash_rejected(env):
    ident = env.contract.create_charter(**charter())
    with pytest.raises(env.vm.UserError,match="stale or wrong"):
        env.contract.propose(ident,"Candidate",controls(),"wrong")


def test_changed_repo_not_allowlisted(env):
    ident = env.contract.create_charter(**charter())
    bad = json.loads(controls());bad[0]["source_url"] = bad[0]["source_url"].replace("example-org/controls", "attacker/controls")
    with pytest.raises(env.vm.UserError,match="not allowlisted"):
        env.contract.propose(ident,"Sub",json.dumps(bad),env.contract.get_charter(ident)["charter_hash"])


def test_moving_branch_rejected(env):
    ident = env.contract.create_charter(**charter())
    bad = json.loads(controls());bad[0]["source_url"] = bad[0]["source_url"].replace("a"*40,"main")
    with pytest.raises(env.vm.UserError,match="pinned"):
        env.contract.propose(ident,"Sub",json.dumps(bad),env.contract.get_charter(ident)["charter_hash"])


def test_duplicate_source_inflation_rejected(env):
    ident = env.contract.create_charter(**charter())
    bad = json.loads(controls());bad[1]["source_url"] = bad[0]["source_url"]
    with pytest.raises(env.vm.UserError,match="duplicate source"):
        env.contract.propose(ident,"Sub",json.dumps(bad),env.contract.get_charter(ident)["charter_hash"])


def test_invalid_dimension_objective_rejected(env):
    args = charter();dims = json.loads(args["dimensions_json"]);dims[0]["failure_mode"] = " "*10
    args["dimensions_json"] = json.dumps(dims)
    with pytest.raises(env.vm.UserError): env.contract.create_charter(**args)


def test_dimension_id_dup_rejected(env):
    args = charter();dims = json.loads(args["dimensions_json"]);dims[1]["id"] = dims[0]["id"]
    args["dimensions_json"] = json.dumps(dims)
    with pytest.raises(env.vm.UserError,match="duplicate"):
        env.contract.create_charter(**args)


def test_no_support_cannot_count_as_covered(env):
    _, cid, fp = setup(env)
    bad = passing(); bad["dimensions"][1]["supports"] = []
    env.nondet.leader = bad
    with pytest.raises(env.vm.UserError,match="malformed"):
        env.contract.assess(cid,fp)


def test_duplicate_support_rejected(env):
    _, cid, fp = setup(env)
    bad = passing(); bad["dimensions"][0]["supports"] = [0,0]
    env.nondet.leader = bad
    with pytest.raises(env.vm.UserError,match="malformed"):
        env.contract.assess(cid,fp)


def test_missing_dimension_rejected(env):
    _, cid, fp = setup(env)
    bad = passing();bad["dimensions"] = bad["dimensions"][:1]
    env.nondet.leader = bad
    with pytest.raises(env.vm.UserError,match="malformed"):
        env.contract.assess(cid,fp)


def test_support_mismatch_causes_disagreement(env):
    _, cid, fp = setup(env)
    bad = passing();bad["dimensions"][0]["supports"] = [0,1]
    env.nondet.validator = bad
    with pytest.raises(env.vm.UserError,match="CONSENSUS"):
        env.contract.assess(cid,fp)


def test_reject_pending_only_owner(env):
    _, cid, fp = setup(env)
    env.gl.message.sender_address = env.B
    with pytest.raises(env.vm.UserError,match="only charter owner"):
        env.contract.reject_pending(cid,fp)
    env.gl.message.sender_address = env.A
    assert env.contract.reject_pending(cid,fp)
    assert env.contract.get_candidate(cid)["status"] == env.mod.OWNER_REJECTED
    with pytest.raises(env.vm.UserError): env.contract.assess(cid,fp)


def test_candidate_replay_assessment_rejected(env):
    _, cid, fp = setup(env)
    env.contract.assess(cid,fp)
    with pytest.raises(env.vm.UserError,match="not awaiting"):
        env.contract.assess(cid,fp)


def test_ratification_hash_guard(env):
    _, cid, fp = setup(env)
    env.contract.assess(cid,fp)
    with pytest.raises(env.vm.UserError,match="assessment hash mismatch"):
        env.contract.ratify(cid,"00","")


def test_active_state_optimistic_concurrency_guard(env):
    _, cid, fp = setup(env)
    env.contract.assess(cid,fp)
    with pytest.raises(env.vm.UserError,match="stale active"):
        env.contract.ratify(cid,env.contract.get_candidate(cid)["assessment_hash"],"bogus")


def test_automatic_expiry(env):
    charter_id,cid,cert=approve(env)
    env.gl.message_raw["datetime"]="2026-10-30T12:00:00Z"
    assert not env.contract.is_active(charter_id,cid,cert,env.contract.get_charter(charter_id)["charter_hash"])
    assert env.contract.get_certificate(cid)["is_current"] is False


def test_owner_revocation_and_replay(env):
    charter_id,cid,cert=approve(env)
    env.gl.message.sender_address=env.B
    with pytest.raises(env.vm.UserError,match="only charter owner"):
        env.contract.revoke(cid,cert)
    env.gl.message.sender_address=env.A
    with pytest.raises(env.vm.UserError,match="certificate mismatch"):
        env.contract.revoke(cid,"fake")
    assert env.contract.revoke(cid,cert)
    assert not env.contract.is_active(charter_id,cid,cert,env.contract.get_charter(charter_id)["charter_hash"])
    assert env.contract.get_candidate(cid)["status"] == env.mod.REVOKED
    with pytest.raises(env.vm.UserError): env.contract.revoke(cid,cert)


def test_superseding_invalidates_old_consumer_pin(env):
    charter_id,first,cert1=approve(env)
    c = env.contract.get_charter(charter_id)
    second=env.contract.propose(charter_id,"Alternative 2",controls(),c["charter_hash"])
    fp=env.contract.get_candidate(second)["candidate_hash"]
    env.contract.assess(second,fp)
    cert2=env.contract.ratify(second,env.contract.get_candidate(second)["assessment_hash"],cert1)
    assert env.contract.get_candidate(first)["status"]==env.mod.SUPERSEDED
    assert not env.contract.is_active(charter_id,first,cert1,c["charter_hash"])
    assert env.contract.is_active(charter_id,second,cert2,c["charter_hash"])
    assert cert1 != cert2


def test_old_assessment_cannot_be_ratified(env):
    _,cid,fp=setup(env)
    env.contract.assess(cid,fp)
    env.gl.message_raw["datetime"] = "2026-10-19T12:00:00Z"
    with pytest.raises(env.vm.UserError,match="too old"):
        env.contract.ratify(cid,env.contract.get_candidate(cid)["assessment_hash"],"")


def test_no_invalid_json_parse_in_contract_state(env):
    _,cid,_=setup(env)
    assert env.contract.get_candidate(cid)["assessment"] is None


def test_unknown_ids_safe_in_gate(env):
    assert not env.contract.is_active(999,888,"hash","hash")
    with pytest.raises(env.vm.UserError): env.contract.get_candidate(999)


def test_baseline_bound_in_charter_hash(env):
    a=charter();b=charter();b["baseline"]+=" Only supervised emergency actions."
    x=env.contract.create_charter(**a); y=env.contract.create_charter(**b)
    assert env.contract.get_charter(x)["charter_hash"]!=env.contract.get_charter(y)["charter_hash"]


def test_source_sha_binds_candidate_hash(env):
    cid=env.contract.create_charter(**charter()); c=env.contract.get_charter(cid)
    c1=env.contract.propose(cid,"Sub",controls(),c["charter_hash"])
    changed=json.loads(controls());changed[1]["source_sha256"]="f"*64
    c2=env.contract.propose(cid,"Sub",json.dumps(changed),c["charter_hash"])
    assert env.contract.get_candidate(c1)["candidate_hash"]!=env.contract.get_candidate(c2)["candidate_hash"]


def test_malformed_leader_bool_as_int_support_rejected(env):
    _,cid,fp=setup(env);bad=passing();bad["dimensions"][0]["supports"]=[True]
    env.nondet.leader=bad
    with pytest.raises(env.vm.UserError):env.contract.assess(cid,fp)


def test_owner_cannot_approve_malformed_result(env):
    _,cid,fp=setup(env);bad=passing();bad["reason_code"]="ALL_COVERED_EXTRA"
    env.nondet.leader=bad
    with pytest.raises(env.vm.UserError):env.contract.assess(cid,fp)
    with pytest.raises(env.vm.UserError):env.contract.ratify(cid,"","")


def test_shared_registry_has_no_fixed_global_spam_cap(env):
    # A permissionless attacker must not be able to fill a globally capped table
    # and permanently prevent everyone else from creating a charter.
    for _ in range(130):
        cid = env.contract.create_charter(**charter())
    assert cid == 130


def test_validator_refetch_detects_mutated_bytes(env):
    _, candidate, fp = setup(env)
    original = env.nondet.get
    state = {"reads": 0}
    def source_mutates_for_validator(url):
        state["reads"] += 1
        if state["reads"] == 3:
            env.nondet.files[ROUTE+"gateway.yml"] = b"tampered evidence"*5
        return original(url)
    env.gl.nondet.web.get=source_mutates_for_validator
    with pytest.raises(env.vm.UserError,match="CONSENSUS REJECTED"):
        env.contract.assess(candidate,fp)
    assert env.contract.get_candidate(candidate)["status"] == env.mod.SUBMITTED
    assert state["reads"] >= 3
