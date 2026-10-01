import unittest
import tempfile
from pathlib import Path
import numpy as np
from core.synchronized_features import extract_window, version_registry, generate
from core.fault_type_feature_contract import reference_statistics, reference_fft
from core.synchronized_raw import read_recording
from test_synchronized_raw import config
import pandas as pd


class FeatureTests(unittest.TestCase):
    def setUp(self):
        self.x=np.random.default_rng(42).normal(size=(10000,5)); self.settings={"variant":"historical105"}
    def test_historical_reference(self):
        v=extract_window(self.x,fs=10000,rpm="8000rpm",settings=self.settings)
        blocks=[]
        s=reference_statistics(self.x); f=reference_fft(self.x,"8000rpm")
        for j in range(5): blocks.extend(s[j]); blocks.extend(f[j] if j in [1,2,3] else [])
        np.testing.assert_allclose(v,blocks)
    def test_corrected_only_declared_positions(self):
        a=extract_window(self.x,fs=10000,rpm="8000rpm",settings=self.settings)
        b=extract_window(self.x,fs=10000,rpm="8000rpm",settings={"variant":"corrected_formulas"})
        allowed={offset+j for offset in [0,15,40,65,90] for j in [6,7]}
        self.assertTrue(set(np.flatnonzero(a != b)).issubset(allowed))
    def test_single_axis_isolation(self):
        a=extract_window(self.x,fs=10000,rpm="8000rpm",settings=self.settings)
        self.x[:,2]*=2
        b=extract_window(self.x,fs=10000,rpm="8000rpm",settings=self.settings)
        self.assertTrue(set(np.flatnonzero(a != b)).issubset(set(range(40,65))))
    def test_constant_zero_negative_peak_and_dc(self):
        for value in [0.,2.,-2.]:
            v=extract_window(np.full((10000,5),value),fs=10000,rpm="6000rpm",settings={"variant":"corrected_formulas"})
            self.assertTrue(np.isfinite(v).all()); self.assertEqual(v[1],value)
        signal=np.sin(2*np.pi*100*np.arange(10000)/10000)*3
        x=np.column_stack([signal]*5)
        v=extract_window(x,fs=10000,rpm="6000rpm",settings=self.settings)
        self.assertAlmostEqual(v[30],3); self.assertAlmostEqual(v[0],3/np.sqrt(2))
    def test_registry_settings_change_identity(self):
        a=version_registry({"variant":"aligned_only","quality":{"a":1}})
        b=version_registry({"variant":"aligned_only","quality":{"a":2}})
        self.assertNotEqual(a["feature_version"],b["feature_version"])
    def test_sidecar_maps_sha_and_raw_count(self):
        with tempfile.TemporaryDirectory() as folder:
            root=Path(folder); path=root/"raw.csv"; cfg=config(10000)
            cfg.update(rpm="8000rpm",label="8screws",acquisition_timestamp="2026-10-01T08:00:00+08:00",attestation="fixture")
            cfg["windows"]["length"]=10000; cfg["windows"]["stride"]=10000
            pd.DataFrame({"time":np.arange(10000)/10000,**{name:self.x[:,j] for j,name in enumerate(["current","x","y","z","delta_t"])}}).to_csv(path,index=False)
            result=generate([(path,cfg)],settings={"variant":"aligned_only"},output=root/"output",incoming_root=root)
            row=result["manifest"]["feature_files"][0]["windows"][0]
            self.assertEqual(row["source_interval"],[0,10000]); self.assertEqual(row["raw_source_sha256"],read_recording(path,cfg).sha256)
            self.assertEqual(len(result["registry"]["columns"]),105)
            self.assertEqual(result["registry"]["settings"]["windows"],cfg["windows"])
    def test_invalid_fft_and_fs_reject(self):
        with self.assertRaises(ValueError): extract_window(self.x,fs=8000,rpm="6000rpm",settings=self.settings)
        with self.assertRaises(ValueError): extract_window(self.x[:2],fs=10000,rpm="6000rpm",settings={"variant":"aligned_only"})
