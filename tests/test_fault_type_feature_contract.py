import unittest
import numpy as np
import pandas as pd
from core.fault_type_feature_contract import reference_statistics, reference_fft, feature_contract
from core.formal_data import _statistical_features, _fft_features


class ContractTests(unittest.TestCase):
    def test_signed_signal_historical_quirks_preserved(self):
        data = np.array([[-10., 2.], [1., 3.], [2., 4.], [1., 8.]])
        reference = reference_statistics(data)
        np.testing.assert_allclose(reference, _statistical_features(pd.DataFrame(data)))
        np.testing.assert_allclose(reference[:, 7], reference[:, 9])
        np.testing.assert_allclose(reference[:, 12], reference[:, 0]**2)
        self.assertLess(reference[0, 6], 10/reference[0, 0])

    def test_fft_amplitude_and_actual_axis(self):
        t = np.arange(10000)/10000
        signal = np.column_stack([2*np.sin(2*np.pi*133*t), 5*np.sin(2*np.pi*266*t)])
        value = _fft_features(pd.DataFrame(signal), "8000rpm")
        np.testing.assert_allclose(value, reference_fft(signal, "8000rpm"), atol=1e-12)
        self.assertAlmostEqual(value[0, 0], 2.)
        self.assertAlmostEqual(value[1, 1], 5.)

    def test_nominal_not_measured_and_physical_unknown(self):
        value = feature_contract()
        self.assertEqual(len(value["columns"]), 105)
        self.assertEqual(value["fft"]["base_hz"]["8000rpm"], 133)
        self.assertIsNone(value["physical_contract"]["orientation"])
