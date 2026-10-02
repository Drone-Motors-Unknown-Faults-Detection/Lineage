"""Analytic SGL gradient/bounds, determinism, failed-state and role guards."""
import copy
import tempfile
from pathlib import Path
from types import SimpleNamespace
import unittest
from unittest.mock import patch
import numpy as np
from core.fault_type_continuous import margin_problem,margin_loss_grad
from core.fault_type_smooth_margin import smooth_loss_grad,solve,projected_gradient
from core.fault_type_final_guard import seal,digest
from experiments.fault_type_solver_diagnosis import audit,verify_cell,METHODS,run,check


class SmoothMarginTests(unittest.TestCase):
    def setUp(self):
        self.y=np.repeat([0,1,2],4)
        self.X=np.random.default_rng(42).normal(size=(12,5))
        self.problem=margin_problem(self.X,self.y)
    def test_finite_difference(self):
        w=np.array([.3,.7,1.,1.2,.4]);_,g=smooth_loss_grad(w,self.problem)
        eps=1e-6
        numeric=[(smooth_loss_grad(w+np.eye(5)[i]*eps,self.problem)[0]-smooth_loss_grad(w-np.eye(5)[i]*eps,self.problem)[0])/(2*eps) for i in range(5)]
        np.testing.assert_allclose(g,numeric,rtol=1e-5,atol=1e-6)
    def test_uniform_approximation_bound(self):
        for w in [np.zeros(5),np.ones(5),np.arange(5.)]:
            h=margin_loss_grad(w,self.problem)[0];s=smooth_loss_grad(w,self.problem)[0]
            self.assertGreaterEqual(s-h,-1e-12)
            self.assertLessEqual(s-h,.5*.1*np.log(2)+1e-12)
    def test_extreme_stable(self):
        v,g=smooth_loss_grad(np.ones(5)*1e5,self.problem)
        self.assertTrue(np.isfinite(v) and np.isfinite(g).all())
    def test_bad_tau(self):
        for t in [0,-1,np.nan,np.inf]:
            with self.assertRaises(ValueError):smooth_loss_grad(np.ones(5),self.problem,tau=t)
    def test_same_hard_objective(self):
        r=solve(self.X,self.y,maxiter=1)
        self.assertEqual(r["same_hard_loss"],r["final_loss"])
        self.assertFalse(r["success"])
        self.assertEqual(len(r["weights"]),5)
    def test_deterministic_nonnegative(self):
        a=solve(self.X,self.y,smooth=True);b=solve(self.X,self.y,smooth=True)
        self.assertEqual(a["weights_checksum"],b["weights_checksum"])
        self.assertTrue(np.all(np.asarray(a["weights"])>=0))
        self.assertLessEqual(a["final_loss"],a["initial_loss"])
    def test_projection(self):
        np.testing.assert_equal(projected_gradient(np.array([0,0,1]),np.array([3,-2,4])),[0,-2,4])
    def test_train_role_guard(self):
        t=[{"sample_id":"a","label":"healthy","t_code":"T1"}]
        m={"motor_roles":{"train":"T1","calibration":"T2","test":"T3"},"manifest_checksum":"x",
           "records":t}
        with patch("experiments.fault_type_solver_diagnosis.records_for",return_value=[]):
            a=audit(t,["a"],m,["healthy"])
        self.assertEqual(a["test_input_ids"],[])
        for key,value in [("t_code","T3"),("label","unknown")]:
            bad=copy.deepcopy(t);bad[0][key]=value
            with self.assertRaises(ValueError):audit(bad,["a"],m,["healthy"])
    def test_cal_test_alias_rejected(self):
        t=[{"sample_id":"a","label":"healthy","t_code":"T1"}]
        m={"motor_roles":{"train":"T1","calibration":"T2","test":"T3"},"manifest_checksum":"m"}
        with patch("experiments.fault_type_solver_diagnosis.records_for",return_value=[t[0]]):
            with self.assertRaises(ValueError):audit(t,["a"],m,["healthy"])
    def test_subset_outside_train(self):
        t=[{"sample_id":"a","label":"healthy","t_code":"T1"}]
        m={"motor_roles":{"train":"T1","calibration":"T2","test":"T3"},"manifest_checksum":"m"}
        with patch("experiments.fault_type_solver_diagnosis.records_for",return_value=[]):
            with self.assertRaises(ValueError):audit(t,["test"],m,["healthy"])
    def test_wall_budget_preserves_failure(self):
        with patch("core.fault_type_smooth_margin.time.perf_counter",side_effect=[0,2,3]):
            r=solve(self.X,self.y,seconds=1)
        self.assertFalse(r["success"]);self.assertEqual(r["status"],"WALL_BUDGET")
        self.assertTrue(r["state_is_last_evaluation_not_converged_iterate"])
        self.assertEqual(len(r["weights"]),5)
    def test_checkpoint_tamper(self):
        p={"protocol_checksum":"p"};expected={"metric_fit_ids":["a"]}
        opt={"weights":[1.]*69,"weights_checksum":digest([1.]*69),"maxiter":150,"maxfun":500,"tau":None}
        c=seal({"protocol_checksum":"p","audit":expected,"method":METHODS[0],"optimizer":opt},"checkpoint_checksum")
        verify_cell(c,p,expected,METHODS[0])
        for key in ["protocol_checksum","audit","method"]:
            bad=copy.deepcopy(c);bad[key]="tampered";bad=seal(bad,"checkpoint_checksum")
            with self.assertRaises(ValueError):verify_cell(bad,p,expected,METHODS[0])
        bad=copy.deepcopy(c);bad["optimizer"]["weights"][0]=2;bad=seal(bad,"checkpoint_checksum")
        with self.assertRaises(ValueError):verify_cell(bad,p,expected,METHODS[0])
    def test_forbidden_protocol_roles_even_resealed(self):
        p={"version":"train_only_solver_diagnosis_v1","methods":METHODS,"seeds":[0,1,2],
           "selection_policy":"none","selection_sample_ids":[],"calibration_fit_ids":[],"test_input_ids":[]}
        for k in ["selection_sample_ids","calibration_fit_ids","test_input_ids"]:
            bad=copy.deepcopy(p);bad[k]=["test"]
            with self.assertRaises(ValueError):check(seal(bad,"protocol_checksum"))
    def test_runner_only_loads_train_and_resumes(self):
        train=[{"sample_id":str(i),"label":str(i//4),"t_code":"T1","rpm":"r"} for i in range(12)]
        m={"fold_id":"f","manifest_checksum":"m","motor_roles":{"train":"T1","calibration":"T2","test":"T3"}}
        q={"known_labels":["0","1","2"]};pa={"fold_id":"f","seed":0,"sha256":"parent"}
        p={"protocol_checksum":"p","budget":{"total_seconds":1800,"reserve_C_bytes":0,"per_fit_seconds":120}}
        calls=[]
        def load(records):
            self.assertEqual(records,train);calls.append(records)
            return np.ones((12,105))
        pools=SimpleNamespace(root=Path("."),load=load)
        parent={"references":{"harmonic69/mixed":{"transformer":SimpleNamespace(transform=lambda X:X[:,:69])}}}
        opt={"weights":[1.]*69,"weights_checksum":digest([1.]*69),"success":False,
             "iterations":150,"same_hard_loss":1.,"message":"controlled failure"}
        with tempfile.TemporaryDirectory() as tmp:
            with patch("experiments.fault_type_solver_diagnosis.check",return_value=(q,None,[m],{"artifacts":[pa]},None)), \
                 patch("experiments.fault_type_solver_diagnosis.verify_sources",return_value="fixed"), \
                 patch("experiments.fault_type_solver_diagnosis.records_for",side_effect=lambda m,role:train if role=="train" else []), \
                 patch("experiments.fault_type_solver_diagnosis.load_bundle",return_value=parent), \
                 patch("experiments.fault_type_solver_diagnosis.solve",side_effect=lambda X,y,**kw:dict(opt,maxiter=kw["maxiter"],maxfun=kw["maxfun"],tau=.1 if kw["smooth"] else None)) as fit:
                a=run(pools,protocol=p,output=Path(tmp));b=run(pools,protocol=p,output=Path(tmp))
                self.assertEqual(a["diagnosis_checksum"],b["diagnosis_checksum"])
                self.assertEqual(fit.call_count,3)
                self.assertEqual(a["outer_evaluations"],0)
                self.assertEqual(a["converged_by_method"],dict.fromkeys([v["id"] for v in METHODS],0))
        self.assertEqual(len(calls),2)


if __name__=="__main__":unittest.main()
