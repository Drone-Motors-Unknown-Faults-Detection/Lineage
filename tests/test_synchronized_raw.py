import copy
import tempfile
import unittest
from pathlib import Path
import numpy as np
import pandas as pd
from core.synchronized_raw import read_recording, audit_timebase, quality_mask, make_windows


def config(n=20):
    return {"recording_id": "fixture-r", "motor_id": "fixture-m", "session_id": "fixture-s", "run_id": "fixture-r", "synthetic": True,
        "raw_sample_count": n, "sample_rate_hz": 10000,
        "parser": {"layout": "single_file_shared_rows", "delimiter": ",", "header_row_0_based": 0,
            "expected_columns": ["time", "current", "x", "y", "z", "delta_t"], "time_column": "time", "time_semantics": "relative_seconds",
            "channels": {k:k for k in ["current", "x", "y", "z", "delta_t"]}},
        "evidence": {k:{"level":"fixture_attested", "reference":"synthetic clock"} for k in ["sample_rate", "alignment"]},
        "quality": {"absolute_bounds":{"x":[-10,10]}}, "windows": {"length":10, "stride":10, "gap_rule":"reject", "bad_point_rule":"reject"}}


class RawTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory(); self.root=Path(self.tmp.name); self.path=self.root/"r.csv"
        self.frame=pd.DataFrame({"time": np.arange(20)/10000, **{k:np.ones(20) for k in ["current","x","y","z","delta_t"]}})
        self.cfg=config()
    def tearDown(self): self.tmp.cleanup()
    def read(self):
        self.frame.to_csv(self.path,index=False)
        return read_recording(self.path,self.cfg)
    def test_deterministic_shared_windows(self):
        r=self.read(); a=audit_timebase(r); q=quality_mask(r,self.cfg["quality"])
        w,_=make_windows(r,a,q,self.cfg["windows"])
        self.assertEqual([v.window_id for v in w],[v.window_id for v in make_windows(r,a,q,self.cfg["windows"])[0]])
        self.assertEqual(w[1].source_interval,(10,20)); self.assertTrue(a.summary["physical_time_alignment_verified"])
    def test_bad_point_preserves_indices(self):
        self.frame.loc[3,"x"]=50; r=self.read(); a=audit_timebase(r); q=quality_mask(r,self.cfg["quality"])
        w,bad=make_windows(r,a,q,self.cfg["windows"])
        self.assertEqual(q.reasons["fixed_bounds"],[[3,1]]); self.assertEqual(len(r.values),20)
        self.assertEqual(w[0].source_interval,(10,20)); self.assertEqual(bad[0]["source_interval"],[0,10])
    def test_duplicate_reverse_gap_drift(self):
        for delta in [0,-.0001,.0002,.0001002]:
            self.frame.loc[4,"time"]=self.frame.loc[3,"time"]+delta
            r=self.read(); a=audit_timebase(r)
            self.assertFalse(a.summary["physical_time_alignment_verified"])
            self.assertTrue(make_windows(r,a,quality_mask(r,{}),self.cfg["windows"])[1])
    def test_documented_not_verified_and_missing_fs(self):
        for cfg in [copy.deepcopy(self.cfg),copy.deepcopy(self.cfg)]:
            cfg["evidence"]["alignment"]["level"]="documented"
            self.frame.to_csv(self.path,index=False)
            self.assertFalse(audit_timebase(read_recording(self.path,cfg)).summary["physical_time_alignment_verified"])
        self.cfg["sample_rate_hz"]=None; self.assertFalse(audit_timebase(self.read()).summary["uniform_sampling_attested"])
    def test_header_count_format_and_separate_channels(self):
        self.frame.to_csv(self.path,index=False)
        for key,value in [("header_row_0_based",1),("layout","separate_files")]:
            cfg=copy.deepcopy(self.cfg); cfg["parser"][key]=value
            with self.assertRaises((ValueError,KeyError)): read_recording(self.path,cfg)
        self.cfg["raw_sample_count"]=19
        with self.assertRaises(ValueError): self.read()
    def test_recording_boundaries_no_merge(self):
        self.frame=self.frame.iloc[:9]; self.cfg["raw_sample_count"]=9
        for rid in ["a","b"]:
            self.cfg["recording_id"]=rid; r=self.read()
            self.assertEqual(make_windows(r,audit_timebase(r),quality_mask(r,{}),self.cfg["windows"])[0],[])
    def test_relative_time_no_timestamp_and_quality_fit_audit(self):
        self.cfg["parser"].pop("time_column"); r=self.read()
        self.assertEqual(audit_timebase(r).summary["time_scope"],"relative_sample_time")
        with self.assertRaises(ValueError): quality_mask(r,{},trained_quality_model={"fit_partition":"test"})
    def test_nan_and_sample_index_gap(self):
        self.frame.loc[5,"y"]=np.nan; r=self.read()
        self.assertEqual(quality_mask(r,{}).reasons["nonfinite"],[[5,2]])
        r.sample_indices[8:]+=1
        self.assertIn(7,audit_timebase(r).summary["bad_edge_indices"])
    def test_tab_header_explicit(self):
        self.path.write_text("preamble\n"+self.frame.to_csv(index=False,sep="\t"),encoding="utf-8",newline="")
        self.cfg["parser"].update(delimiter="\t",header_row_0_based=1)
        r=read_recording(self.path,self.cfg); self.assertEqual(r.original_lines_1_based[0],3)
