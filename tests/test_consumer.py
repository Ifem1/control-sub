"""Consumer permission checks with a fake IC transport, never claiming real IC-to-IC runtime."""
import importlib.util
import sys
from pathlib import Path
from types import SimpleNamespace
import pytest
from test_contract import approve


def _consumer(env, charter_id, root, action="abc123"):
    fake=sys.modules["genlayer"]
    # Mimic the transport layer only. Permission decisions come from the REAL
    # underlying ControlSub Python code, not a separately fabricated boolean.
    fake.gl.contract_interface=lambda iface: (lambda address: SimpleNamespace(view=lambda:env.contract))
    path=Path(__file__).resolve().parents[1]/"contracts"/"controlsub_consumer.py"
    spec=importlib.util.spec_from_file_location("controlsub_consumer_test",path)
    module=importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module.ControlSubConsumer("0x"+"aa"*20,charter_id,root,action)


def test_consumer_executes_once_only_for_live_certificate(env):
    char,candidate,cert=approve(env)
    root=env.contract.get_charter(char)["charter_hash"]
    consumer=_consumer(env,char,root)
    with pytest.raises(env.vm.UserError,match="action hash"):
        consumer.execute(candidate,cert,"changed-action")
    assert consumer.execute(candidate,cert,"abc123") is True
    assert consumer.get_execution()["candidate_id"] == candidate
    with pytest.raises(env.vm.UserError,match="already executed"):
        consumer.execute(candidate,cert,"abc123")


def test_consumer_does_not_accept_wrong_or_revoked_certificate(env):
    char,candidate,cert=approve(env)
    root=env.contract.get_charter(char)["charter_hash"]
    consumer=_consumer(env,char,root)
    with pytest.raises(env.vm.UserError,match="not actively certified"):
        consumer.execute(candidate,"bogus","abc123")
    env.contract.revoke(candidate,cert)
    with pytest.raises(env.vm.UserError,match="not actively certified"):
        consumer.execute(candidate,cert,"abc123")
    assert consumer.get_execution()["executed"] is False


def test_consumer_pins_charter_hash_at_constructor(env):
    char,candidate,cert=approve(env)
    consumer=_consumer(env,char,"wrong-charter-hash")
    with pytest.raises(env.vm.UserError,match="not actively certified"):
        consumer.execute(candidate,cert,"abc123")


def test_consumer_owner_cannot_bypass_certificate(env):
    char,candidate,cert=approve(env)
    root=env.contract.get_charter(char)["charter_hash"]
    consumer=_consumer(env,char,root)
    env.gl.message.sender_address=env.B
    with pytest.raises(env.vm.UserError,match="owner only"):
        consumer.execute(candidate,cert,"abc123")
    env.gl.message.sender_address=env.A
    env.gl.message_raw["datetime"]="2026-12-01T12:00:00Z"
    with pytest.raises(env.vm.UserError,match="not actively certified"):
        consumer.execute(candidate,cert,"abc123")
