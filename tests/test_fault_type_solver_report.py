import unittest
import numpy as np
from core.fault_type_continuous import margin_problem,margin_loss_grad
from core.fault_type_smooth_margin import smooth_loss_grad,projected_gradient
from experiments.fault_type_solver_report import verify_losses


class SolverReportTests(unittest.TestCase):
    def fixture(self,smooth):
        X=np.random.default_rng(7).normal(size=(12,5));p=margin_problem(X,np.repeat([0,1,2],4))
        w=np.ones(5);v,g=(smooth_loss_grad if smooth else margin_loss_grad)(w,p)
        return p,{"weights":w.tolist(),"final_loss":v,"same_hard_loss":margin_loss_grad(w,p)[0],
                  "projected_gradient_inf":float(np.abs(projected_gradient(w,g)).max())}
    def test_hard_numeric_recomputation(self):
        p,r=self.fixture(False);self.assertEqual(verify_losses(r,p,False)["final_loss"],r["final_loss"])
    def test_smooth_numeric_recomputation(self):
        p,r=self.fixture(True);self.assertEqual(verify_losses(r,p,True)["final_loss"],r["final_loss"])
    def test_tampered_loss(self):
        for key in ["final_loss","same_hard_loss","projected_gradient_inf"]:
            p,r=self.fixture(True);r[key]+=1
            with self.assertRaises(ValueError):verify_losses(r,p,True)
    def test_tampered_weights(self):
        p,r=self.fixture(False);r["weights"][0]+=1
        with self.assertRaises(ValueError):verify_losses(r,p,False)


if __name__=="__main__":unittest.main()
