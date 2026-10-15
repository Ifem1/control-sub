"""Small executable reference controls for the ControlSub demo.

This module demonstrates the two charter requirements in code. It is not a
production identity provider, credential store, or deployment service.
"""


class ControlViolation(ValueError):
    """Raised when a protected operation would bypass a required control."""


def authenticate(*, hardware_credential_verified: bool, password_only: bool) -> bool:
    """Accept only a verified hardware-bound credential; no password fallback."""
    if password_only or not hardware_credential_verified:
        raise ControlViolation("hardware-bound authentication is required")
    return True


def activate_production(*, deployer: str, reviewer: str,
                        reviewer_authorized: bool, review_approved: bool) -> bool:
    """Activate only after an authorized, independent review has approved."""
    if not reviewer_authorized or not review_approved:
        raise ControlViolation("authorized reviewer approval is required")
    if not deployer or not reviewer or deployer == reviewer:
        raise ControlViolation("reviewer must be independent of the deployer")
    return True
