import copy
import unittest
import numpy as np
from core.fault_type_final_guard import seal
from experiments.fault_type_model_selection import CANDIDATES, run, select_candidate


class SpyPool:
    def __init__(self): self.loaded = []
    def load(self, rows):
        self.loaded.extend(r["sample_id"] for r in rows)
        if any(r["sample_id"].startswith("test") for r in rows): raise AssertionError("test loaded before lock")
        return np.array([np.arange(105)*.01+int(r["label"] != "8screws")*3+int(r["sample_id"][-1])*.001 for r in rows])


def manifests():
    result = []
    for fold in range(3):
        records = [{"sample_id": f"{split}-{fold}-{i}", "label": label} for split in ["train", "validation", "test"]
            for i, label in enumerate(["8screws", "8screws", "1screws", "1screws"])]
        result.append({"records": records, "healthy_label": "8screws", "known_fault_labels": ["1screws"],
            "sample_ids": {split: [r["sample_id"] for r in records if r["sample_id"].startswith(split)] for split in ["train", "validation", "test"]},
            "fold_id": str(fold), "sample_split_seed": [42, 123, 2026][fold], "manifest_checksum": f"checksum{fold}"})
    return result


class SelectionTests(unittest.TestCase):
    def test_known_only_spy_and_determinism(self):
        m = manifests()
        registry = seal({"candidates": CANDIDATES, "manifests": [{"manifest_checksum": x["manifest_checksum"]} for x in m]}, "registry_checksum")
        pool = SpyPool()
        a = run(pool, manifests=m, registry=registry)
        b = run(SpyPool(), manifests=m, registry=registry)
        self.assertFalse(any(s.startswith("test") for s in pool.loaded))
        self.assertEqual(a["selected_candidate"], b["selected_candidate"])
        self.assertEqual(a["scores"], b["scores"])
        self.assertEqual(len(a["fold_results"]), 9)
        self.assertTrue(all(not audit["test_selection_ids"] for audit in a["fit_audits"]))

    def test_unknown_validation_forbidden(self):
        m = manifests(); m[0]["records"][4]["label"] = "unknown"
        registry = seal({"candidates": CANDIDATES, "manifests": [{"manifest_checksum": x["manifest_checksum"]} for x in m]}, "registry_checksum")
        pool = SpyPool()
        with self.assertRaises(ValueError): run(pool, manifests=m, registry=registry)
        self.assertEqual(pool.loaded, [])

    def test_tie_prefers_linear_and_ba_secondary(self):
        rows = [{"candidate": c["name"], "macro_f1": .5, "balanced_accuracy": .5} for c in CANDIDATES]
        self.assertEqual(select_candidate(rows, CANDIDATES)[0], "linear_baseline")
        rows[1]["balanced_accuracy"] = .6
        self.assertEqual(select_candidate(rows, CANDIDATES)[0], "rbf_svm")

    def test_changed_candidate_registry_rejected(self):
        m = manifests(); candidates = copy.deepcopy(CANDIDATES); candidates[1]["parameters"]["C"] = 100
        registry = seal({"candidates": candidates, "manifests": [{"manifest_checksum": x["manifest_checksum"]} for x in m]}, "registry_checksum")
        with self.assertRaises(ValueError): run(SpyPool(), manifests=m, registry=registry)
