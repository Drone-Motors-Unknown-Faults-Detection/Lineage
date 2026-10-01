import copy
import unittest
import numpy as np
from core.fault_type_leakage import numeric_duplicates, selection_dependency, audit_fit_ids


class LeakageAuditTests(unittest.TestCase):
    def test_exact_and_semantic_copies_do_not_imply_physical_identity(self):
        rows=[{"sample_id": str(i), "source_file": f"copy{i}.csv", "label": str(i), "t_code": f"T{i}"} for i in range(3)]
        values=np.ones((3,105)); values[2,0]=1+1e-13
        report,_=numeric_duplicates(rows,values)
        self.assertEqual(report["exact_numeric"]["rows_in_duplicate_groups"],2)
        self.assertEqual(report["semantic_12g"]["rows_in_duplicate_groups"],3)
        self.assertEqual(report["exact_numeric"]["cross_label_groups"],1)
        self.assertIn("not proof",report["limitation"])

    def test_signed_zero_exact_numeric_and_input_validation(self):
        rows=[{"sample_id":str(i),"source_file":str(i),"label":"h","t_code":"T"} for i in range(2)]
        values=np.zeros((2,105)); values[1,0]=-0.0
        self.assertEqual(numeric_duplicates(rows,values)[0]["exact_numeric"]["duplicate_groups"],1)
        with self.assertRaises(ValueError): numeric_duplicates(rows,values[:,:104])

    def test_global_selection_reuses_other_folds_test_but_local_does_not(self):
        folds=[{"fold_id": "a", "sample_ids":{"validation":["v"],"test":["t"]}},
               {"fold_id": "b", "sample_ids":{"validation":["t"],"test":["v"]}}]
        global_audit=selection_dependency(folds)
        self.assertEqual(global_audit["status"],"NOT_INDEPENDENT_FOR_GLOBAL_SELECTION")
        self.assertTrue(all(r["own_fold_selection_overlap"]==0 and r["effective_selection_test_overlap"]==1 for r in global_audit["folds"]))
        self.assertEqual(selection_dependency(folds,global_choice=False)["status"],"NO_RECORDED_SELECTION_TEST_ID_OVERLAP")

    def test_fit_audit_rejects_unknown_test_and_missing_inventory(self):
        m={"fold_id":"a","healthy_label":"h","known_fault_labels":["k"],
           "records":[{"sample_id":s,"label":l} for s,l in [("x","h"),("v","k"),("t","u")]],
           "sample_ids":{"train":["x"],"validation":["v"],"calibration":["v"],"test":["t"]}}
        base={"fold_id":"a","train_only_transform_fit_ids":["x"],"classifier_fit_ids":["x"],"reference_ids":["x"],
              "selection_ids":["v"],"calibration_ids":["v"]}
        audits=[dict(base,representation=name) for name in ["baseline105","vibration75","current15","delta_t15","vibration_current90","train_pca20"]]
        self.assertEqual(audit_fit_ids(audits,[m])["status"],"PASS")
        bad=copy.deepcopy(audits); bad[0]["classifier_fit_ids"]=["t"]
        self.assertEqual(audit_fit_ids(bad,[m])["checks"][0]["status"],"FAIL")
        self.assertEqual(audit_fit_ids(audits[:-1],[m])["status"],"FAIL")
