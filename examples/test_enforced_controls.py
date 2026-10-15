"""Behavior checks for the executable ControlSub reference controls."""
import unittest

from enforced_controls import ControlViolation, activate_production, authenticate


class EnforcedControlTests(unittest.TestCase):
    def test_hardware_authentication_passes(self):
        self.assertTrue(authenticate(hardware_credential_verified=True, password_only=False))

    def test_password_only_authentication_is_rejected(self):
        with self.assertRaises(ControlViolation):
            authenticate(hardware_credential_verified=False, password_only=True)

    def test_independent_approved_review_passes(self):
        self.assertTrue(activate_production(deployer="alice", reviewer="bob",
                                            reviewer_authorized=True, review_approved=True))

    def test_activation_without_approval_is_rejected(self):
        with self.assertRaises(ControlViolation):
            activate_production(deployer="alice", reviewer="bob",
                                reviewer_authorized=True, review_approved=False)

    def test_deployer_cannot_review_own_activation(self):
        with self.assertRaises(ControlViolation):
            activate_production(deployer="alice", reviewer="alice",
                                reviewer_authorized=True, review_approved=True)


if __name__ == "__main__":
    unittest.main()
