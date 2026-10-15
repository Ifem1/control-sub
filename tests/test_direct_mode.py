"""GenLayer real Direct Mode VM scenarios (requires genlayer-test 0.29.2).

These are not run by the pure-Python mock harness and must pass in GenVM.
Run: pytest tests/test_direct_mode.py -v
"""
import json
from pathlib import Path
from fixtures import charter, controls, passing, missing, SOURCES, ROUTE

ROOT = Path(__file__).resolve().parents[1]


def _warp(direct_vm, value="2026-10-15T12:00:00Z"):
    direct_vm.warp(value)
    import sys
    module = sys.modules.get("genlayer.gl")
    if module is not None and getattr(module, "message_raw", None) is not None:
        module.message_raw["datetime"] = value


def _deploy(direct_vm, direct_deploy, direct_alice):
    direct_vm.check_pickling = True
    direct_vm.sender = direct_alice
    _warp(direct_vm)
    return direct_deploy(str(ROOT/"contracts"/"controlsub.py"), sdk_version="v0.2.12")


def _open(contract):
    args = charter()
    ident=contract.create_charter(args["title"],args["context"],args["baseline"],
                                  args["dimensions_json"],args["allowed_repos_json"],
                                  args["certificate_lifetime_days"])
    root = contract.get_charter(ident)["charter_hash"]
    candidate=contract.propose(ident,"Pinned alternative",controls(),root)
    return ident,candidate,root,contract.get_candidate(candidate)["candidate_hash"]


def _mocks(direct_vm, assessment):
    direct_vm.mock_web(r"/gateway\.yml$",{
        "status":200,"body":SOURCES[0].decode("utf-8")
    })
    direct_vm.mock_web(r"/review\.yml$",{
        "status":200,"body":SOURCES[1].decode("utf-8")
    })
    direct_vm.mock_llm(r"CONTROLSUB /",json.dumps(assessment))


def test_direct_accept_and_owner_ratification(direct_vm, direct_deploy, direct_alice, direct_bob):
    obj=_deploy(direct_vm,direct_deploy,direct_alice)
    charter_id,candidate,root,fp=_open(obj)
    _mocks(direct_vm,passing())
    assert obj.assess(candidate,fp) == 2
    direct_vm.sender = direct_bob
    with direct_vm.expect_revert("only charter owner"):
        obj.ratify(candidate,obj.get_candidate(candidate)["assessment_hash"],"")
    direct_vm.sender=direct_alice
    cert=obj.ratify(candidate,obj.get_candidate(candidate)["assessment_hash"],"")
    assert obj.is_active(charter_id,candidate,cert,root)
    assert obj.get_certificate(candidate)["is_current"]


def test_direct_rejects_substantive_gap(direct_vm, direct_deploy, direct_alice):
    obj=_deploy(direct_vm,direct_deploy,direct_alice)
    _,candidate,_,fp=_open(obj)
    _mocks(direct_vm,missing())
    assert obj.assess(candidate,fp)==3
    with direct_vm.expect_revert("no independently validated passing assessment"):
        obj.ratify(candidate,obj.get_candidate(candidate)["assessment_hash"],"")


def test_direct_validator_detects_forged_leader_pass(direct_vm, direct_deploy, direct_alice):
    obj=_deploy(direct_vm,direct_deploy,direct_alice)
    _,candidate,_,fp=_open(obj)
    _mocks(direct_vm,passing())
    obj.assess(candidate,fp)
    direct_vm.clear_mocks()
    _mocks(direct_vm,missing())
    assert direct_vm.run_validator() is False
    # Direct Mode does not simulate consensus rollback; test finality separately.


def test_direct_revoke_invalidates_even_identical_hash(direct_vm,direct_deploy,direct_alice):
    obj=_deploy(direct_vm,direct_deploy,direct_alice)
    charter_id,candidate,root,fp=_open(obj)
    _mocks(direct_vm,passing())
    obj.assess(candidate,fp)
    cert=obj.ratify(candidate,obj.get_candidate(candidate)["assessment_hash"],"")
    assert obj.is_active(charter_id,candidate,cert,root)
    assert obj.revoke(candidate,cert)
    assert not obj.is_active(charter_id,candidate,cert,root)


def test_direct_moving_branch_is_not_accepted(direct_vm,direct_deploy,direct_alice):
    obj=_deploy(direct_vm,direct_deploy,direct_alice)
    ident=obj.create_charter(charter()["title"], charter()["context"], charter()["baseline"],
                            charter()["dimensions_json"], charter()["allowed_repos_json"],14)
    src=json.loads(controls());src[0]["source_url"]=src[0]["source_url"].replace("a"*40,"main")
    with direct_vm.expect_revert("pinned 40-hex commit"):
        obj.propose(ident,"Bad source",json.dumps(src),obj.get_charter(ident)["charter_hash"])
