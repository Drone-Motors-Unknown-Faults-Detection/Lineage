import copy
import json
import os
import tempfile
import subprocess
import sys
import unittest
from pathlib import Path
from unittest.mock import patch
from core import durable_exposure as durable
from core.fault_type_final_guard import seal,FinalTestBlocked
from core.fresh_data import prepare_bundle,IncomingStore,load_models
from experiments.synchronized_fixture import run as make_fixture
from experiments.fault_type_fresh import run
from test_fault_type_final_guard import fixture


class TransactionTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory(); self.root=Path(self.tmp.name); self.path=self.root/"ledger.json"
        self.b,self.l,self.c=fixture(); durable.initialize(self.path,self.l)
    def tearDown(self): self.tmp.cleanup()
    def register(self): return durable.register(self.path,self.b,self.c,claim="new_motor",evaluation_id="test",expected_checksum=self.l["ledger_checksum"])
    def test_register_and_resume_binding(self):
        receipt,_=self.register(); self.assertTrue(durable.read(self.path)["evaluations"])
        durable.validate_resume(self.path,receipt,self.b,self.c,evaluation_id="test",claim="new_motor")
        with self.assertRaises(FinalTestBlocked): durable.validate_resume(self.path,receipt,self.b,self.c,evaluation_id="different",claim="new_motor")
        with self.assertRaises(FinalTestBlocked): self.register()
    def test_crash_after_journal_exposure_preserved(self):
        original=durable.atomic_json
        def failing(path,value):
            if path==self.path: raise OSError("simulated head fsync/write failure")
            original(path,value)
        with patch.object(durable,"atomic_json",side_effect=failing):
            with self.assertRaises(OSError): self.register()
        with self.assertRaises(FinalTestBlocked): durable.read(self.path)
        recovered=durable.recover(self.path)
        self.assertEqual(len(recovered["evaluations"]),1)
        with self.assertRaises(FinalTestBlocked): durable.initialize(self.path,self.l)
    def test_rollback_head_detected(self):
        self.register(); durable.atomic_json(self.path,self.l)
        with self.assertRaises(FinalTestBlocked): durable.read(self.path)
        self.assertEqual(len(durable.recover(self.path)["evaluations"]),1)
    def test_concurrent_processes_no_lost_exposure(self):
        for name,value in [("b",self.b),("c",self.c)]: (self.root/f"{name}.json").write_text(json.dumps(value))
        code="from pathlib import Path; import json,sys; from core.durable_exposure import register; root=Path(sys.argv[1]); b=json.loads((root/'b.json').read_text()); c=json.loads((root/'c.json').read_text()); register(root/'ledger.json',b,c,claim='new_motor',evaluation_id=sys.argv[2],expected_checksum=c['exposure_ledger_checksum'])"
        processes=[subprocess.Popen([sys.executable,"-c",code,str(self.root),str(i)],stdout=subprocess.PIPE,stderr=subprocess.PIPE) for i in range(2)]
        codes=[p.communicate(timeout=40) or None for p in processes]
        self.assertEqual(sorted(p.returncode for p in processes),[0,1])
        self.assertEqual(len(durable.read(self.path)["evaluations"]),1)


class FreshTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp=tempfile.TemporaryDirectory(); cls.root=Path(cls.tmp.name)
        make_fixture(cls.root)
        read=lambda name:json.loads((cls.root/name).read_text(encoding="utf-8"))
        cls.m=read("features/manifest.json"); cls.r=read("features/version_registry.json"); cls.c=read("locked_config.json"); cls.l=read("seed_ledger.json")
        cls.bundle=prepare_bundle(cls.root,cls.m,cls.r)
    @classmethod
    def tearDownClass(cls): cls.tmp.cleanup()
    def setup_run(self,name):
        folder=self.root/name; folder.mkdir(); path=folder/"ledger.json"; durable.initialize(path,self.l); return folder,path
    def args(self): return dict(manifest=self.m,registry=self.r,locked=self.c,artifact_root=self.root/"models",claim="new_motor",evaluation_id="fixture-eval")
    def test_actual_root_loader_and_models(self):
        self.assertEqual(IncomingStore(self.root).load(self.bundle["records"]).shape,(300,105))
        fitted,manifests=load_models(self.c,self.root/"models",self.bundle); self.assertEqual(len(fitted),3)
        broken=copy.deepcopy(self.c); broken.pop("training_physical_contract")
        with self.assertRaises(FinalTestBlocked): load_models(seal(broken,"locked_checksum"),self.root/"models",self.bundle)
    def test_schema_version_environment_role_and_columns(self):
        for key,value in [("fresh_protocol","other"),("column_order",[]),("minimum_test_groups_per_class",1),("serialization_environment",{})]:
            c=copy.deepcopy(self.c); c[key]=value
            with self.assertRaises(FinalTestBlocked): load_models(seal(c,"locked_checksum"),self.root/"models",self.bundle)
    def test_sha_and_missing_physical_block_before_load(self):
        with patch("core.fresh_data._sha256_file",return_value="changed"):
            with self.assertRaises(FinalTestBlocked): load_models(self.c,self.root/"models",self.bundle)
        m=copy.deepcopy(self.m); m["physical_contract"]["sensor_units"]=None
        with self.assertRaises(FinalTestBlocked): prepare_bundle(self.root,seal(m,"manifest_checksum"),self.r)
    def test_actual_count_and_no_synthetic_upgrade(self):
        m=copy.deepcopy(self.m); m["raw_recordings"][0]["config"]["raw_sample_count"]+=1
        with self.assertRaises(ValueError): prepare_bundle(self.root,seal(m,"manifest_checksum"),self.r)
        m=copy.deepcopy(self.m); m["synthetic"]=False
        with self.assertRaises(FinalTestBlocked): prepare_bundle(self.root,seal(m,"manifest_checksum"),self.r)
    def test_persist_failure_no_prediction(self):
        folder,path=self.setup_run("persist")
        with patch("experiments.fault_type_fresh.paired_predictions") as prediction,patch.object(durable,"register",side_effect=OSError("disk unavailable")):
            with self.assertRaises(OSError): run(self.root,**self.args(),ledger_path=path,action="evaluate",output=folder)
            prediction.assert_not_called()
    def test_predict_failure_remains_exposed_and_resume_config_blocked(self):
        folder,path=self.setup_run("failed")
        with patch("experiments.fault_type_fresh.paired_predictions",side_effect=RuntimeError("predict failed")):
            with self.assertRaises(RuntimeError): run(self.root,**self.args(),ledger_path=path,action="evaluate",output=folder)
        self.assertEqual(len(durable.read(path)["evaluations"]),1)
        receipt=json.loads((folder/"exposure_receipt.json").read_text())
        changed=copy.deepcopy(self.c); changed["scope"]="changed"; changed=seal(changed,"locked_checksum")
        with self.assertRaises(FinalTestBlocked): durable.validate_resume(path,receipt,self.bundle,changed,evaluation_id="fixture-eval",claim="new_motor")
    def test_subprocess_cli_validate_evaluate_resume(self):
        folder,path=self.setup_run("cli")
        env=dict(os.environ,PYTHONIOENCODING="utf-8",MPLCONFIGDIR=str(folder/"mpl"))
        args=["--ledger",str(path),"--incoming-root",str(self.root),"--manifest",str(self.root/"features/manifest.json"),
            "--registry",str(self.root/"features/version_registry.json"),"--locked",str(self.root/"locked_config.json"),
            "--training-artifacts",str(self.root/"models"),"--claim","new_motor","--evaluation-id","fixture-cli"]
        def cli(action,extra=[]):
            result=subprocess.run([sys.executable,"-m","experiments.fault_type_fresh",action,*args,*extra],capture_output=True,text=True,encoding="utf-8",env=env,timeout=60)
            self.assertEqual(result.returncode,0,result.stderr)
        report=folder/"report.json"; cli("validate",["--report-output",str(report)])
        self.assertEqual(json.loads(report.read_text())["status"],"PREPARED_NO_PREDICTIONS"); self.assertFalse(durable.read(path).get("evaluations"))
        cli("evaluate",["--report-output",str(report)])
        result=json.loads(report.read_text(encoding="utf-8")); self.assertEqual(len(result["runs"]),6)
        self.assertTrue(result["synthetic_engineering"]); self.assertFalse(result["final_independent_validation_completed"])
        receipt=folder/"receipt.json"; receipt.write_text(json.dumps(result["exposure_receipt"]))
        cli("resume",["--resume-receipt",str(receipt),"--report-output",str(report)])
        self.assertEqual(len(durable.read(path)["evaluations"]),1)
