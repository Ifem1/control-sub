# { "Depends": "py-genlayer:1jb45aa8ynh2a9c9xn3b7qqh8sm5q93hwfp7jqmwsfhh8jpz09h6" }
"""Minimal genuine IC-to-IC consumer example. Not a frontend or a substitute oracle."""
from genlayer import *
from typing import Any, cast


@gl.contract_interface
class IControlSub:
    class View:
        def is_active(self, charter_id: u256, candidate_id: u256,
                      expected_certificate_hash: str, expected_charter_hash: str) -> bool: ...


class ControlSubConsumer(gl.Contract):
    """Only performs a sealed action when the pinned live substitute remains active.

    The owner may never turn this guard off; the only way to perform its action
    is a genuine typed cross-contract read against ControlSub current state.
    """
    controlsub_address: Address
    owner: Address
    charter_id: u256
    charter_hash: str
    action_hash: str
    executed: bool
    consumed_candidate_id: u256
    consumed_certificate_hash: str

    def __init__(self, controlsub_address: Address, charter_id: u256,
                 charter_hash: str, action_hash: str):
        if not charter_hash or not action_hash:
            raise gl.vm.UserError("both exact charter and action hashes are required")
        self.controlsub_address = controlsub_address
        self.owner = gl.message.sender_address
        self.charter_id = charter_id
        self.charter_hash = charter_hash
        self.action_hash = action_hash
        self.executed = False
        self.consumed_candidate_id = u256(0)
        self.consumed_certificate_hash = ""

    @gl.public.write
    def execute(self, candidate_id: u256, certificate_hash: str, expected_action_hash: str) -> bool:
        if gl.message.sender_address != self.owner:
            raise gl.vm.UserError("owner only")
        if self.executed:
            raise gl.vm.UserError("action already executed")
        if expected_action_hash != self.action_hash:
            raise gl.vm.UserError("action hash mismatch")
        if not certificate_hash:
            raise gl.vm.UserError("missing certificate")
        # GenLayer's proxy is dynamically implemented by the SDK; this explicit
        # boundary cast retains the typed interface above without losing strict
        # typing for the consumer's own state and arguments.
        substitution: Any = cast(Any, IControlSub(self.controlsub_address))
        if not substitution.view().is_active(self.charter_id, candidate_id,
                                             certificate_hash, self.charter_hash):
            raise gl.vm.UserError("substitute not actively certified")
        self.executed = True
        self.consumed_candidate_id = candidate_id
        self.consumed_certificate_hash = certificate_hash
        return True

    @gl.public.view  # type: ignore[reportUnknownMemberType]  # SDK decorator has no strict typing
    def get_execution(self) -> dict[str, Any]:
        return {"owner": str(self.owner), "executed": self.executed,
                "candidate_id": int(self.consumed_candidate_id),
                "certificate_hash": self.consumed_certificate_hash,
                "charter_id": int(self.charter_id), "charter_hash": self.charter_hash,
                "action_hash": self.action_hash}
