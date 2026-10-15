"""Local deterministic stub of the GenLayer API (not a GenVM simulation)."""
import importlib.util
import sys
import types
from pathlib import Path
from types import SimpleNamespace
import pytest

A = "0x" + "11" * 20
B = "0x" + "22" * 20
C = "0x" + "33" * 20


class TreeMap(dict):
    @classmethod
    def __class_getitem__(cls, key):
        return cls


class Return:
    def __init__(self, calldata):
        self.calldata = calldata


class VM:
    class UserError(Exception):
        pass
    Return = Return

    def __init__(self):
        self.last_validator = None
        self.leader_response = None
        self.agree = True

    def run_nondet_unsafe(self, leader, validator):
        self.leader_response = leader()
        self.last_validator = validator
        self.agree = validator(Return(self.leader_response))
        if not self.agree:
            raise self.UserError("CONSENSUS REJECTED")
        return self.leader_response


class Nondet:
    def __init__(self):
        self.files = {}
        self.leader = None
        self.validator = None
        self.calls = []
        self.fetch_calls = []

    class Reply:
        def __init__(self, body):
            self.body = body

    def get(self, url):
        self.fetch_calls.append(url)
        if url not in self.files:
            raise RuntimeError("web unavailable")
        return self.Reply(self.files[url])

    def exec_prompt(self, prompt, response_format=None):
        self.calls.append(prompt)
        assert response_format == "json"
        return self.validator if "INDEPENDENT VALIDATOR" in prompt and self.validator is not None else self.leader


@pytest.fixture
def env(monkeypatch):
    module = types.ModuleType("genlayer")
    machine = VM()
    nondet = Nondet()
    gl = SimpleNamespace(
        public=SimpleNamespace(write=lambda fn: fn, view=lambda fn: fn),
        Contract=object, contract_interface=lambda cls: cls,
        vm=machine,
        nondet=SimpleNamespace(web=SimpleNamespace(get=nondet.get), exec_prompt=nondet.exec_prompt),
        message=SimpleNamespace(sender_address=A,
                                raw=SimpleNamespace(datetime="2026-10-15T12:00:00Z")))
    module.gl = gl
    module.TreeMap = TreeMap
    module.Address = str
    module.u8 = int
    module.u32 = int
    module.u256 = int
    module.allow_storage = lambda klass: klass
    monkeypatch.setitem(sys.modules, "genlayer", module)
    target = Path(__file__).resolve().parents[1] / "contracts" / "controlsub.py"
    spec = importlib.util.spec_from_file_location("controlsub_under_test", target)
    imported = importlib.util.module_from_spec(spec)
    monkeypatch.setitem(sys.modules, spec.name, imported)
    spec.loader.exec_module(imported)
    contract = imported.ControlSub()
    return SimpleNamespace(mod=imported, contract=contract, gl=gl, vm=machine,
                           nondet=nondet, A=A, B=B, C=C)
