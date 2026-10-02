import unittest
from experiments.fault_type_mechanism_diagnosis import distribution


class DiagnosticCases(unittest.TestCase):
    def test_signed_distribution(self):
        self.assertEqual(distribution([-3,0,3])['median'],0)
        self.assertEqual(distribution([-3,0,3])['min'],-3)

    def test_empty_not_fake_zero(self):
        self.assertEqual(distribution([]),{'n':0})

    def test_invalid_rejected(self):
        for x in [[float('nan')],[float('inf')],[[1,2]]]:
            with self.assertRaises(ValueError):distribution(x)
