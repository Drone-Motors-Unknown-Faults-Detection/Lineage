"""Versioned no-selection overlays; never mutate historical manifests/locks."""
from __future__ import annotations

import copy
from core.fault_type_final_guard import digest, verify_seal
from core.fault_type_leakage import selection_dependency
from core.fault_type_validator import compute_manifest_checksum, validate_split_manifest, assert_valid_for_formal

PROTOCOL = "fixed_methods_motor_calibration_v1"


def fixed_manifests(priors, protocol):
    verify_seal(protocol, "protocol_checksum")
    if protocol["protocol_version"] != PROTOCOL or protocol["selection_policy"] != "none":
        raise ValueError("fixed no-selection protocol required")
    if len(priors) != len(protocol["folds"]) or len(priors) != 3:
        raise ValueError("all three motor folds required")
    result = []
    for prior, binding in zip(priors, protocol["folds"]):
        if (prior["manifest_checksum"] != binding["prior_manifest_checksum"] or
            prior["dataset_fingerprint"] != protocol["dataset_fingerprint"] or
            prior["healthy_label"] != protocol["healthy_label"] or
            prior["known_fault_labels"] != protocol["known_fault_labels"] or
            prior["unknown_test_labels"] != protocol["unknown_test_labels"]):
            raise ValueError("prior class/source binding mismatch")
        assert_valid_for_formal(prior, allow_incomplete=True)
        for part, checksum in binding["partition_id_checksums"].items():
            if digest(prior["sample_ids"][part]) != checksum:
                raise ValueError("partition binding mismatch")
        m = copy.deepcopy(prior)
        m.pop("manifest_checksum", None)
        m.update(schema_version=2, protocol_version=PROTOCOL, protocol_checksum=protocol["protocol_checksum"],
                 prior_manifest_checksum=prior["manifest_checksum"], selection_policy="none",
                 selection_sample_ids=[], shared_validation_calibration=False,
                 motor_roles=binding["motors"], fold_id=f"fixed-fold{binding['fold']}",
                 sample_split_seed=None, historical_test_exposed=True, validation_status="N/A_NO_SELECTION")
        m["sample_ids"]["validation"] = []
        m["campaigns"]["validation"] = None
        m["expected_counts"]["validation"] = {}
        m["actual_counts"]["validation"] = {}
        m["group_counts"]["validation"] = {}
        m["limitations"] = [s for s in m["limitations"] if "Validation and calibration reuse" not in s]
        m["limitations"].append("All rows historically test-exposed; fixed method CV rotation is exploratory, not fresh validation.")
        m["split_id"] = "fixed-v1-"+compute_manifest_checksum(m)[:20]
        m["validator"] = validate_split_manifest(m, verify_checksum=False)
        m["manifest_checksum"] = compute_manifest_checksum(m)
        assert_valid_for_formal(m, allow_incomplete=True)
        result.append(m)
    return result


def audit_fixed_fit(audit, manifest):
    """Require exact input identities, not merely disjointness from final test."""
    assert_valid_for_formal(manifest, allow_incomplete=True)
    if manifest.get("protocol_version") != PROTOCOL:
        raise ValueError("not fixed motor protocol")
    expected = {"scaler_fit_ids": "train", "representation_fit_ids": "train",
                "classifier_fit_ids": "train", "reference_fit_ids": "train",
                "covariance_fit_ids": "train", "neighbor_reference_ids": "train",
                "calibration_sample_ids": "calibration"}
    for key, part in expected.items():
        if audit.get(key) != manifest["sample_ids"][part]:
            raise ValueError(f"{key} must exactly match {part}")
    if (audit.get("selection_sample_ids") != [] or audit.get("selection_policy") != "none" or
        audit.get("shared_validation_calibration") is not False or
        any(key in audit for key in ("global_winner", "selected_representation"))):
        raise ValueError("selection/shared calibration forbidden")
    if audit.get("manifest_checksum") != manifest["manifest_checksum"]:
        raise ValueError("fit audit manifest checksum mismatch")
    return {"status": "VERIFIED_INPUT_USE", "evidence": "runtime record IDs at fit/cal calls; no claim of raw acquisition independence"}


def fixed_dependency(manifests):
    for m in manifests:
        assert_valid_for_formal(m, allow_incomplete=True)
    result = selection_dependency(manifests,
        selection_by_fold={m["fold_id"]: set(m["selection_sample_ids"]) for m in manifests}, global_choice=False)
    result["selector"] = "none"
    result["cross_fold_role_rotation"] = "allowed for fixed-method CV; not a global selector"
    result["historical_test_exposed"] = all(m.get("historical_test_exposed") for m in manifests)
    return result
