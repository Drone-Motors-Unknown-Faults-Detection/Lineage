import unittest
from core.fault_type_final_guard import FinalTestBlocked, seal
from experiments.fault_type_controlled_eval import run


class NoTestPool:
    def load(self, records): raise AssertionError("test loaded before permission check")


class EvalTests(unittest.TestCase):
    def test_unlocked_fails_before_load(self):
        ledger = seal({}, "ledger_checksum")
        locked = seal({"status": "not_locked", "exposure_ledger_checksum": ledger["ledger_checksum"]}, "locked_checksum")
        with self.assertRaises(FinalTestBlocked): run(NoTestPool(), manifests=[], locked=locked, ledger=ledger, fitted=[], exploratory=True)

    def test_old_data_cannot_be_implicit_fresh(self):
        ledger = seal({}, "ledger_checksum")
        locked = seal({"status": "locked", "exposure_ledger_checksum": ledger["ledger_checksum"]}, "locked_checksum")
        with self.assertRaises(FinalTestBlocked): run(NoTestPool(), manifests=[], locked=locked, ledger=ledger, fitted=[])
