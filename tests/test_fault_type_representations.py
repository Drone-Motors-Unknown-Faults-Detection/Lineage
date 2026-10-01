import copy
import tempfile
import unittest
from pathlib import Path
import numpy as np
from core.fault_type_final_guard import seal
from experiments.fault_type_representations import Representation,CANDIDATES,build_registry,run


class Pool:
    def __init__(self): self.loaded=[]
    def load(self,records):
        if any(r["partition"]=="test" for r in records): raise AssertionError("test accessed by representation selection")
        self.loaded.extend(r["sample_id"] for r in records)
        return np.vstack([np.random.default_rng(r["number"]).normal(size=105)+r["class_id"] for r in records])


def manifests():
    result=[]; labels=["8screws","1screws","2screws","3screws","3_14screws","4screws"]
    for fold,seed in enumerate([42,123,2026]):
        records=[]; ids={p:[] for p in ["train","validation","calibration","test"]}
        for part,count in [("train",10),("validation",5),("test",1)]:
            for j,label in enumerate(labels):
                for i in range(count):
                    number=len(records)+fold*1000; sid=str(number); ids[part].append(sid)
                    records.append({"sample_id":sid,"partition":part,"number":number,"label":label,"class_id":j})
        ids["calibration"]=ids["validation"][:]
        result.append({"healthy_label":"8screws","known_fault_labels":labels[1:],"unknown_test_labels":["4_146screws","5screws","6screws","7screws"],
            "sample_split_seed":seed,"fold_id":str(fold),"manifest_checksum":str(fold),"dataset_fingerprint":"fixture","records":records,"sample_ids":ids})
    return result


class RepresentationTests(unittest.TestCase):
    def test_indices_and_train_only_transform(self):
        X=np.random.default_rng(42).normal(size=(60,105))
        for candidate in CANDIDATES:
            t=Representation(candidate).fit(X); before=t.transform_checksum
            transformed=t.transform(X+999)
            self.assertEqual(before,t.transform_checksum)
            self.assertEqual(transformed.shape[1],candidate["pca_components"] or len(candidate["indices"]))
    def test_unknown_selection_and_changed_registry_reject(self):
        m=manifests(); registry=build_registry(m); m[0]["records"][60]["label"]="7screws"
        with tempfile.TemporaryDirectory() as folder:
            with self.assertRaises(ValueError): run(Pool(),manifests=m,registry=registry,output=Path(folder))
            m=manifests(); changed=copy.deepcopy(build_registry(m)); changed["candidates"][0]["indices"]=[]
            with self.assertRaises(ValueError): run(Pool(),manifests=m,registry=seal(changed,"registry_checksum"),output=Path(folder))
    def test_selection_never_loads_test_and_saves_all_candidates(self):
        m=manifests(); pool=Pool()
        with tempfile.TemporaryDirectory() as folder:
            result=run(pool,manifests=m,registry=build_registry(m),output=Path(folder))
            self.assertEqual(len(result["training_artifacts"]),18)
            self.assertEqual(result["status"],"locked")
